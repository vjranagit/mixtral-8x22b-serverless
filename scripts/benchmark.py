#!/usr/bin/env python3
"""
Performance Benchmarking Script for Mixtral-8x22B API

Tests throughput (tokens/second), latency, and concurrency.

Usage:
    python scripts/benchmark.py --endpoint https://api.runpod.ai/v2/xxx
    python scripts/benchmark.py --endpoint https://api.runpod.ai/v2/xxx --concurrent 10
    python scripts/benchmark.py --endpoint prod  # Uses prod endpoint from .env
"""

import argparse
import asyncio
import json
import os
import time
from datetime import datetime
from statistics import mean, median, stdev
from typing import List, Dict, Tuple

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Install with: pip install httpx")
    exit(1)


class BenchmarkConfig:
    """Benchmark configuration"""

    # Test prompts of varying lengths
    PROMPTS = {
        "short": "Say hello.",
        "medium": "Explain the concept of machine learning in 100 words.",
        "long": "Write a detailed technical explanation of how mixture of experts models work, including their architecture, training process, and advantages over dense models. Include specific examples.",
    }

    # Default parameters
    DEFAULT_MAX_TOKENS = 512
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_CONCURRENT_REQUESTS = 5
    DEFAULT_NUM_REQUESTS = 10


class Benchmark:
    """Benchmarking tool for Mixtral API"""

    def __init__(self, endpoint_url: str, api_key: str = None):
        self.endpoint_url = endpoint_url.rstrip('/')
        self.api_key = api_key or os.getenv('API_KEY', 'test-key')
        self.results: List[Dict] = []

    async def make_request(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> Dict:
        """Make a single request and measure performance"""

        start_time = time.time()

        payload = {
            "input": {
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.endpoint_url}/run",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                data = response.json()

            end_time = time.time()
            total_time = end_time - start_time

            # Extract metrics
            output = data.get('output', {})
            tokens = output.get('tokens', {})

            result = {
                "success": True,
                "total_time": total_time,
                "prompt_tokens": tokens.get('prompt', 0),
                "completion_tokens": tokens.get('completion', 0),
                "total_tokens": tokens.get('total', 0),
                "text_length": len(output.get('text', '')),
            }

            # Calculate tokens per second
            if result['completion_tokens'] > 0 and total_time > 0:
                result['tokens_per_second'] = result['completion_tokens'] / total_time
            else:
                result['tokens_per_second'] = 0

            return result

        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "total_time": end_time - start_time,
                "error": str(e),
                "tokens_per_second": 0
            }

    async def run_sequential(
        self,
        prompt: str,
        num_requests: int = 10,
        max_tokens: int = 512
    ) -> List[Dict]:
        """Run sequential requests"""

        print(f"\nRunning {num_requests} sequential requests...")
        results = []

        for i in range(num_requests):
            print(f"  Request {i+1}/{num_requests}...", end='', flush=True)
            result = await self.make_request(prompt, max_tokens)
            results.append(result)

            if result['success']:
                print(f" ✓ {result['total_time']:.2f}s, {result['tokens_per_second']:.1f} tok/s")
            else:
                print(f" ✗ Error: {result.get('error', 'Unknown')}")

        return results

    async def run_concurrent(
        self,
        prompt: str,
        num_requests: int = 10,
        concurrent: int = 5,
        max_tokens: int = 512
    ) -> List[Dict]:
        """Run concurrent requests"""

        print(f"\nRunning {num_requests} requests with concurrency {concurrent}...")
        results = []

        # Create batches
        batches = [
            list(range(i, min(i + concurrent, num_requests)))
            for i in range(0, num_requests, concurrent)
        ]

        for batch_idx, batch in enumerate(batches):
            print(f"  Batch {batch_idx+1}/{len(batches)} ({len(batch)} requests)...", end='', flush=True)

            tasks = [
                self.make_request(prompt, max_tokens)
                for _ in batch
            ]

            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

            success_count = sum(1 for r in batch_results if r['success'])
            print(f" ✓ {success_count}/{len(batch)} succeeded")

        return results

    def calculate_statistics(self, results: List[Dict]) -> Dict:
        """Calculate statistics from results"""

        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]

        if not successful:
            return {
                "total_requests": len(results),
                "successful": 0,
                "failed": len(failed),
                "error_rate": 100.0
            }

        latencies = [r['total_time'] for r in successful]
        tps_values = [r['tokens_per_second'] for r in successful if r['tokens_per_second'] > 0]
        total_tokens = [r['total_tokens'] for r in successful]
        completion_tokens = [r['completion_tokens'] for r in successful]

        stats = {
            "total_requests": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "error_rate": (len(failed) / len(results) * 100) if results else 0,

            "latency": {
                "mean": mean(latencies),
                "median": median(latencies),
                "min": min(latencies),
                "max": max(latencies),
                "stdev": stdev(latencies) if len(latencies) > 1 else 0,
                "p95": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
                "p99": sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0,
            },

            "throughput": {
                "mean_tps": mean(tps_values) if tps_values else 0,
                "median_tps": median(tps_values) if tps_values else 0,
                "min_tps": min(tps_values) if tps_values else 0,
                "max_tps": max(tps_values) if tps_values else 0,
            },

            "tokens": {
                "total_tokens_mean": mean(total_tokens) if total_tokens else 0,
                "completion_tokens_mean": mean(completion_tokens) if completion_tokens else 0,
            }
        }

        return stats

    def print_report(self, stats: Dict, prompt_type: str = "unknown"):
        """Print benchmark report"""

        print("\n" + "="*70)
        print(f"  BENCHMARK RESULTS - {prompt_type.upper()} PROMPT")
        print("="*70)

        print(f"\nRequests:")
        print(f"  Total: {stats['total_requests']}")
        print(f"  Successful: {stats['successful']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Error Rate: {stats['error_rate']:.1f}%")

        if stats['successful'] > 0:
            lat = stats['latency']
            print(f"\nLatency (seconds):")
            print(f"  Mean: {lat['mean']:.3f}s")
            print(f"  Median: {lat['median']:.3f}s")
            print(f"  Min: {lat['min']:.3f}s")
            print(f"  Max: {lat['max']:.3f}s")
            print(f"  P95: {lat['p95']:.3f}s")
            print(f"  P99: {lat['p99']:.3f}s")
