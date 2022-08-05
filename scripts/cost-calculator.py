#!/usr/bin/env python3
"""
Cost Calculator for Mixtral-8x22B Serverless Deployment

Calculates GPU costs, storage costs, and revenue projections for the
Mixtral-8x22B inference API on RunPod Serverless.

Usage:
    python scripts/cost-calculator.py --days 1
    python scripts/cost-calculator.py --days 30 --budget 500
    python scripts/cost-calculator.py --detailed
"""

import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, Optional


# ============================================================================
# COST CONSTANTS
# ============================================================================

class CostConfig:
    """Cost configuration for RunPod H100 deployment"""

    # GPU Costs (4x H100 80GB)
    GPU_COST_PER_HOUR = 2.40        # $2.40/hour for 4x H100
    GPU_COST_PER_SECOND = GPU_COST_PER_HOUR / 3600

    # Storage Costs
    STORAGE_COST_PER_GB_PER_MONTH = 0.20
    STORAGE_SIZE_GB = 200          # Network volume size

    # Revenue (OpenRouter pricing)
    REVENUE_INPUT_PER_MILLION = 0.50    # $0.50 per M input tokens
    REVENUE_OUTPUT_PER_MILLION = 1.30   # $1.30 per M output tokens
    REVENUE_PER_REQUEST = 0.001          # $0.001 per request

    # OpenRouter Fee
    OPENROUTER_FEE_PERCENT = 5.5

    # Typical Request Characteristics
    AVG_INPUT_TOKENS = 1000
    AVG_OUTPUT_TOKENS = 500
    AVG_GENERATION_TIME_SECONDS = 30


class CostCalculator:
    """Calculate costs for Mixtral-8x22B deployment"""

    def __init__(self, config: CostConfig = None):
        self.config = config or CostConfig()

    def calculate_gpu_cost(self, hours: float) -> float:
        """Calculate GPU cost for given hours"""
        return hours * self.config.GPU_COST_PER_HOUR

    def calculate_storage_cost(self, days: int) -> float:
        """Calculate storage cost for given days"""
        months = days / 30.0
        return (self.config.STORAGE_SIZE_GB *
                self.config.STORAGE_COST_PER_GB_PER_MONTH *
                months)

    def calculate_request_cost(self,
                               num_requests: int,
                               avg_duration_seconds: float = None) -> float:
        """Calculate cost per number of requests"""
        duration = avg_duration_seconds or self.config.AVG_GENERATION_TIME_SECONDS
        total_seconds = num_requests * duration
        return total_seconds * self.config.GPU_COST_PER_SECOND

    def calculate_revenue(self,
                          num_requests: int,
                          input_tokens: int = None,
                          output_tokens: int = None) -> Dict[str, float]:
        """Calculate revenue and profit from requests"""
        input_tokens = input_tokens or self.config.AVG_INPUT_TOKENS
        output_tokens = output_tokens or self.config.AVG_OUTPUT_TOKENS

        # Revenue per request
        input_revenue = (input_tokens / 1_000_000) * self.config.REVENUE_INPUT_PER_MILLION
        output_revenue = (output_tokens / 1_000_000) * self.config.REVENUE_OUTPUT_PER_MILLION
        request_revenue = self.config.REVENUE_PER_REQUEST

        gross_per_request = input_revenue + output_revenue + request_revenue

        # Total revenue
        total_gross = num_requests * gross_per_request

        # OpenRouter fee
        openrouter_fee = total_gross * (self.config.OPENROUTER_FEE_PERCENT / 100)

        # Net revenue
        net_revenue = total_gross - openrouter_fee

        # Cost
        total_cost = self.calculate_request_cost(num_requests)

        # Profit
        profit = net_revenue - total_cost
        profit_margin = (profit / net_revenue * 100) if net_revenue > 0 else 0

        return {
            "num_requests": num_requests,
            "gross_revenue": total_gross,
            "openrouter_fee": openrouter_fee,
            "net_revenue": net_revenue,
            "gpu_cost": total_cost,
            "profit": profit,
            "profit_margin_percent": profit_margin,
            "per_request": {
                "gross": gross_per_request,
                "net": gross_per_request * (1 - self.config.OPENROUTER_FEE_PERCENT / 100),
                "cost": total_cost / num_requests if num_requests > 0 else 0,
                "profit": profit / num_requests if num_requests > 0 else 0
            }
        }

    def usage_scenario(self,
                       scenario_name: str,
                       active_hours_per_day: float,
                       days: int,
                       avg_requests_per_hour: int = 0) -> Dict:
        """Calculate costs for a usage scenario"""
        total_hours = active_hours_per_day * days
        total_requests = avg_requests_per_hour * total_hours if avg_requests_per_hour > 0 else 0

        gpu_cost = self.calculate_gpu_cost(total_hours)
        storage_cost = self.calculate_storage_cost(days)
        total_cost = gpu_cost + storage_cost

        result = {
            "scenario": scenario_name,
            "period_days": days,
            "active_hours_per_day": active_hours_per_day,
            "total_active_hours": total_hours,
            "costs": {
                "gpu": gpu_cost,
                "storage": storage_cost,
                "total": total_cost
            },
            "cost_per_day": total_cost / days if days > 0 else 0
        }

        if total_requests > 0:
            revenue_data = self.calculate_revenue(total_requests)
            result["requests"] = total_requests
            result["revenue"] = revenue_data
            result["roi_percent"] = ((revenue_data["profit"] / total_cost) * 100) if total_cost > 0 else 0

        return result


def print_cost_report(calculator: CostCalculator, days: int, detailed: bool = False):
    """Print cost analysis report"""

    print("\n" + "="*70)
    print("  MIXTRAL-8x22B SERVERLESS COST ANALYSIS")
    print("="*70)
    print(f"\nPeriod: {days} days")
    print(f"GPU Configuration: 4x H100 80GB @ ${calculator.config.GPU_COST_PER_HOUR}/hour")
    print(f"Storage: {calculator.config.STORAGE_SIZE_GB}GB Network Volume @ ${calculator.config.STORAGE_COST_PER_GB_PER_MONTH}/GB/month")

    print("\n" + "-"*70)
    print("  USAGE SCENARIOS")
    print("-"*70)

    scenarios = [
        ("Light Usage", 2, days, 10),      # 2 hrs/day, 10 req/hr
        ("Moderate Usage", 4, days, 20),   # 4 hrs/day, 20 req/hr
        ("Heavy Usage", 8, days, 30),      # 8 hrs/day, 30 req/hr
        ("Always On (Dev)", 24, days, 5),  # 24/7, low traffic
    ]

    for scenario_name, hours_per_day, period, req_per_hr in scenarios:
        scenario = calculator.usage_scenario(scenario_name, hours_per_day, period, req_per_hr)

        print(f"\n{scenario_name}:")
        print(f"  Active Hours: {scenario['active_hours_per_day']:.1f} hrs/day ({scenario['total_active_hours']:.0f} hrs total)")
        print(f"  GPU Cost: ${scenario['costs']['gpu']:.2f}")
        print(f"  Storage Cost: ${scenario['costs']['storage']:.2f}")
        print(f"  Total Cost: ${scenario['costs']['total']:.2f} (${scenario['cost_per_day']:.2f}/day)")

        if 'revenue' in scenario:
            rev = scenario['revenue']
            print(f"  Requests: {scenario['requests']:,}")
            print(f"  Gross Revenue: ${rev['gross_revenue']:.2f}")
            print(f"  Net Revenue: ${rev['net_revenue']:.2f}")
            print(f"  Profit: ${rev['profit']:.2f} ({rev['profit_margin_percent']:.1f}% margin)")
            print(f"  ROI: {scenario['roi_percent']:.0f}%")

    if detailed:
        print("\n" + "-"*70)
        print("  DETAILED BREAKDOWN")
        print("-"*70)

        print(f"\nPer-Second Costs:")
        print(f"  GPU: ${calculator.config.GPU_COST_PER_SECOND:.6f}/second")

        print(f"\nPer-Request Economics (typical):")
        rev = calculator.calculate_revenue(1)
        print(f"  Input Tokens: {calculator.config.AVG_INPUT_TOKENS:,}")
        print(f"  Output Tokens: {calculator.config.AVG_OUTPUT_TOKENS:,}")
        print(f"  Generation Time: {calculator.config.AVG_GENERATION_TIME_SECONDS}s")
        print(f"  Gross Revenue: ${rev['per_request']['gross']:.4f}")
        print(f"  Net Revenue: ${rev['per_request']['net']:.4f}")
