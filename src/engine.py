import os
import logging
import json
import asyncio

from dotenv import load_dotenv
from typing import AsyncGenerator, Optional
import time

from vllm import AsyncLLMEngine
from vllm.entrypoints.logger import RequestLogger
from vllm.entrypoints.openai.serving_chat import OpenAIServingChat
from vllm.entrypoints.openai.serving_completion import OpenAIServingCompletion
from vllm.entrypoints.openai.protocol import ChatCompletionRequest, CompletionRequest, ErrorResponse
from vllm.entrypoints.openai.serving_models import BaseModelPath, LoRAModulePath, OpenAIServingModels


from utils import DummyRequest, JobInput, BatchSize, create_error_response
from constants import DEFAULT_MAX_CONCURRENCY, DEFAULT_BATCH_SIZE, DEFAULT_BATCH_SIZE_GROWTH_FACTOR, DEFAULT_MIN_BATCH_SIZE
from tokenizer import TokenizerWrapper
from engine_args import get_engine_args

class vLLMEngine:
    def __init__(self, engine = None):
        load_dotenv() # For local development
        self.engine_args = get_engine_args()
        logging.info(f"Engine args: {self.engine_args}")
        
        # Initialize vLLM engine first
        self.llm = self._initialize_llm() if engine is None else engine.llm
        
        # Only create custom tokenizer wrapper if not using mistral tokenizer mode
        # For mistral models, let vLLM handle tokenizer initialization
        if self.engine_args.tokenizer_mode != 'mistral':
            self.tokenizer = TokenizerWrapper(self.engine_args.tokenizer or self.engine_args.model, 
                                              self.engine_args.tokenizer_revision, 
                                              self.engine_args.trust_remote_code)
        else:
            # For mistral models, we'll get the tokenizer from vLLM later
            self.tokenizer = None
            
        self.max_concurrency = int(os.getenv("MAX_CONCURRENCY", DEFAULT_MAX_CONCURRENCY))
        self.default_batch_size = int(os.getenv("DEFAULT_BATCH_SIZE", DEFAULT_BATCH_SIZE))
        self.batch_size_growth_factor = int(os.getenv("BATCH_SIZE_GROWTH_FACTOR", DEFAULT_BATCH_SIZE_GROWTH_FACTOR))
        self.min_batch_size = int(os.getenv("MIN_BATCH_SIZE", DEFAULT_MIN_BATCH_SIZE))

    def _get_tokenizer_for_chat_template(self):
        """Get tokenizer for chat template application"""
        if self.tokenizer is not None:
            return self.tokenizer
        else:
            # For mistral models, get tokenizer from vLLM engine
            # This is a fallback - ideally chat templates should be handled by vLLM directly
            try:
                from transformers import AutoTokenizer
                tokenizer = AutoTokenizer.from_pretrained(
                    self.engine_args.tokenizer or self.engine_args.model,
                    revision=self.engine_args.tokenizer_revision or "main",
                    trust_remote_code=self.engine_args.trust_remote_code
                )
                # Create a minimal wrapper
                class MinimalTokenizerWrapper:
                    def __init__(self, tokenizer):
                        self.tokenizer = tokenizer
                        self.custom_chat_template = os.getenv("CUSTOM_CHAT_TEMPLATE")
                        self.has_chat_template = bool(self.tokenizer.chat_template) or bool(self.custom_chat_template)
                        if self.custom_chat_template and isinstance(self.custom_chat_template, str):
                            self.tokenizer.chat_template = self.custom_chat_template
                    
                    def apply_chat_template(self, input):
                        if isinstance(input, list):
                            if not self.has_chat_template:
                                raise ValueError(
                                    "Chat template does not exist for this model, you must provide a single string input instead of a list of messages"
                                )
                        elif isinstance(input, str):
                            input = [{"role": "user", "content": input}]
                        else:
                            raise ValueError("Input must be a string or a list of messages")
                        
                        return self.tokenizer.apply_chat_template(
                            input, tokenize=False, add_generation_prompt=True
                        )
                
                return MinimalTokenizerWrapper(tokenizer)
            except Exception as e:
                logging.error(f"Failed to create fallback tokenizer: {e}")
                raise e

    def dynamic_batch_size(self, current_batch_size, batch_size_growth_factor):
        return min(current_batch_size*batch_size_growth_factor, self.default_batch_size)
                           
    async def generate(self, job_input: JobInput):
        try:
            async for batch in self._generate_vllm(
                llm_input=job_input.llm_input,
                validated_sampling_params=job_input.sampling_params,
                batch_size=job_input.max_batch_size,
                stream=job_input.stream,
                apply_chat_template=job_input.apply_chat_template,
                request_id=job_input.request_id,
                batch_size_growth_factor=job_input.batch_size_growth_factor,
                min_batch_size=job_input.min_batch_size
            ):
                yield batch
        except Exception as e:
            yield {"error": create_error_response(str(e)).model_dump()}

    async def _generate_vllm(self, llm_input, validated_sampling_params, batch_size, stream, apply_chat_template, request_id, batch_size_growth_factor, min_batch_size: str) -> AsyncGenerator[dict, None]:
        if apply_chat_template or isinstance(llm_input, list):
            tokenizer_wrapper = self._get_tokenizer_for_chat_template()
            llm_input = tokenizer_wrapper.apply_chat_template(llm_input)
        results_generator = self.llm.generate(llm_input, validated_sampling_params, request_id)
        n_responses, n_input_tokens, is_first_output = validated_sampling_params.n, 0, True
        last_output_texts, token_counters = ["" for _ in range(n_responses)], {"batch": 0, "total": 0}

        batch = {
            "choices": [{"tokens": []} for _ in range(n_responses)],
        }
        
        max_batch_size = batch_size or self.default_batch_size
        batch_size_growth_factor, min_batch_size = batch_size_growth_factor or self.batch_size_growth_factor, min_batch_size or self.min_batch_size
        batch_size = BatchSize(max_batch_size, min_batch_size, batch_size_growth_factor)
    

        async for request_output in results_generator:
            if is_first_output:  # Count input tokens only once
                n_input_tokens = len(request_output.prompt_token_ids)
                is_first_output = False

            for output in request_output.outputs:
                output_index = output.index
                token_counters["total"] += 1
                if stream:
                    new_output = output.text[len(last_output_texts[output_index]):]
                    batch["choices"][output_index]["tokens"].append(new_output)
                    token_counters["batch"] += 1

                    if token_counters["batch"] >= batch_size.current_batch_size:
                        batch["usage"] = {
                            "input": n_input_tokens,
                            "output": token_counters["total"],
                        }
                        yield batch
                        batch = {
                            "choices": [{"tokens": []} for _ in range(n_responses)],
                        }
                        token_counters["batch"] = 0
                        batch_size.update()

                last_output_texts[output_index] = output.text

        if not stream:
            for output_index, output in enumerate(last_output_texts):
                batch["choices"][output_index]["tokens"] = [output]
            token_counters["batch"] += 1

        if token_counters["batch"] > 0:
            batch["usage"] = {"input": n_input_tokens, "output": token_counters["total"]}
            yield batch

