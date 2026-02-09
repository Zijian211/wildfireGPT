import argparse
import sys
import os
import json
from datetime import datetime

# --- Add the project root to the Python path ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """
    Command-line test runner for AI Persona Testing (Backend Execution)
    Usage: python run_tests.py --persona all --output results.json
    """
    parser = argparse.ArgumentParser(description="WildfireGPT AI Persona Test Runner")
    parser.add_argument("--persona", type=str, default="all", 
                       help="Persona to test (or 'all' for all personas)")
    parser.add_argument("--output", type=str, default=f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                       help="Output file for results")
    parser.add_argument("--verbose", action="store_true",
                       help="Show detailed output")
    parser.add_argument("--scenario", type=str, default=None,
                       help="Specific scenario ID to test")
    
    args = parser.parse_args()
    
    print("🧪 WildfireGPT AI Persona Test Runner")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {args.persona}")
    print(f"Output: {args.output}")
    print("=" * 60)
    
    try:
        # --- Import test modules ---
        from src.modules.test_scenarios.test_runner import PersonaTestRunner
        from src.modules.test_scenarios.test_cases import get_all_scenarios, get_test_scenario
        
        runner = PersonaTestRunner()
        
        if args.scenario:
            # --- Run specific scenario by ID ---
            print(f"Running specific scenario: {args.scenario}")
            all_scenarios = get_all_scenarios()
            target_scenario = None
            
            for scenario in all_scenarios:
                if scenario["id"] == args.scenario:
                    target_scenario = scenario
                    break
            
            if not target_scenario:
                print(f"❌ Scenario {args.scenario} not found")
                return
            
            result = runner.run_single_test(
                target_scenario["persona"],
                {
                    "id": target_scenario["id"],
                    "question": target_scenario["question"],
                    "expected_aspects": target_scenario["expected_aspects"]
                }
            )
            
            results = [result]
            print(f"✅ Scenario {args.scenario} completed: {result.get('aspect_coverage', 0)}% coverage")
            
        elif args.persona.lower() == "all":
            print("Running comprehensive test of all personas...")
            results = runner.run_all_tests()
            print(f"✅ All tests completed: {len(results)} scenarios")
            
        else:
            print(f"Testing persona: {args.persona}...")
            scenarios = get_test_scenario(args.persona)
            if not scenarios:
                print(f"❌ No test scenarios found for {args.persona}")
                return
            
            results = []
            for scenario in scenarios:
                result = runner.run_single_test(args.persona, scenario)
                results.append(result)
                if args.verbose:
                    print(f"  - {scenario['id']}: {result.get('aspect_coverage', 0)}% coverage, {result.get('response_time', 0)}s")
            
            print(f"✅ {len(results)} tests completed for {args.persona}")
        
        # --- Generate report ---
        report, report_file = runner.generate_report()
        
        # --- Save to specified output file ---
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"📄 Report saved to: {args.output}")
        
        # --- Display summary statistics ---
        print("\n" + "=" * 60)
        print("📊 TEST REPORT SUMMARY")
        print("=" * 60)
        
        if results:
            # --- Calculate summary stats using pandas for convenience ---
            import pandas as pd
            df = pd.DataFrame(results)
            
            total_tests = len(df)
            passed_tests = len(df[df['status'] == 'completed'])
            avg_coverage = df['aspect_coverage'].mean() if 'aspect_coverage' in df.columns else 0
            avg_response_time = df['response_time'].mean() if 'response_time' in df.columns else 0
            
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
            print(f"Average Coverage: {avg_coverage:.1f}%")
            print(f"Average Response Time: {avg_response_time:.2f}s")
            
            # --- Persona breakdown if persona data is available ---
            if 'persona' in df.columns:
                print("\n📈 Performance by Persona:")
                persona_stats = df.groupby('persona').agg({
                    'aspect_coverage': 'mean',
                    'response_time': 'mean',
                    'test_id': 'count'
                }).round(2)
                
                for persona, stats in persona_stats.iterrows():
                    print(f"  {persona}: {stats['aspect_coverage']}% coverage, {stats['response_time']}s avg")
        
        print(f"\n✅ Test execution completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory.")
        print("Required modules: src.test_scenarios.test_runner, src.test_scenarios.test_cases")
        return 1
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())