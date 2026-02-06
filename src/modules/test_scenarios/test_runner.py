import streamlit as st
import pandas as pd
import time
from datetime import datetime
import json
import os
import traceback
from src.modules.test_scenarios.test_cases import get_all_scenarios, get_test_scenario
from src.assistants.assistant_router import AssistantRouter
from src.modules.ui.context_manager import build_enhanced_prompt

class PersonaTestRunner:
    """
    Persona Test Runner
    Dry-run test system for persona scenarios
    """
    def __init__(self):
        self.results = []
        self.test_log = []
        
    # ==========================================
    # --- DEBUG DOCTOR FOR TEST RUNNER ---
    # ==========================================
    def _debug_diagnose_unpacking(self, func_name, data):
        """
        Debug helper to diagnose unpacking errors
        """
        print(f"🔍 DEBUG DOCTOR [{func_name}]:")
        print(f"   Type of data: {type(data)}")
        if isinstance(data, tuple):
            print(f"   Tuple length: {len(data)}")
            for i, item in enumerate(data):
                item_type = type(item)
                item_preview = str(item)[:100] if item is not None else "None"
                print(f"   Item {i}: type={item_type}, preview={item_preview}")
        elif isinstance(data, list):
            print(f"   List length: {len(data)}")
            for i, item in enumerate(data[:3]):  # First 3 items only
                print(f"   Item {i}: type={type(item)}, preview={str(item)[:100]}")
        else:
            print(f"   Value: {str(data)[:200]}")
        print("=" * 50)
        
    def run_single_test(self, persona, test_scenario, mock_session_state=None):
        """
        Run a single test scenario with SAFE unpacking
        """
        print(f"🧪 Testing {persona} - {test_scenario['id']}")
        print(f"📝 Question: {test_scenario['question']}")
    
        # --- Create mock session state if not provided ---
        if mock_session_state is None:
            mock_session_state = {
                "user_persona": persona,
                "messages": [],
                "location_confirmed": True,
                "lat": -33.8688,
                "lon": 151.2093,
                "pending_file_context": None
            }
    
        # --- Initialize assistant ---
        try:
            assistant = AssistantRouter("ChecklistAssistant")
            print(f"✅ Assistant initialized: {type(assistant).__name__}")
        except Exception as e:
            print(f"❌ Failed to initialize assistant: {e}")
            error_result = self._create_error_result(test_scenario, persona, f"Assistant init failed: {e}")
            return error_result
    
        # --- Build enhanced prompt (SAFE UNPACKING) ---
        try:
            prompt_result = build_enhanced_prompt(
                test_scenario["question"], 
                mock_session_state
            )
            self._debug_diagnose_unpacking("build_enhanced_prompt", prompt_result)
            
            # --- Handle all possible return formats ---
            final_prompt = test_scenario["question"]
            badges = []
            
            if isinstance(prompt_result, tuple):
                if len(prompt_result) >= 2:
                    # --- Standard format: (final_prompt, badges) ---
                    final_prompt, badges = prompt_result[0], prompt_result[1]
                elif len(prompt_result) == 1:
                    # Only prompt returned
                    final_prompt = prompt_result[0]
                else:
                    print(f"⚠️ Empty tuple from build_enhanced_prompt")
            else:
                # --- Not a tuple, assume it's just the prompt ---
                final_prompt = prompt_result
                
            print(f"📤 Final prompt length: {len(final_prompt)} chars")
                
        except Exception as e:
            print(f"⚠️ Error in build_enhanced_prompt: {e}")
            final_prompt, badges = test_scenario["question"], []
    
        # --- Get response with SAFE HANDLING ---
        start_time = time.time()
        try:
            print("🤖 Calling get_assistant_response...")
            raw_response = assistant.get_assistant_response(final_prompt)
            response_time = time.time() - start_time
            
            # --- DEBUG: Check what get_assistant_response returns ---
            self._debug_diagnose_unpacking("get_assistant_response", raw_response)
        
            # --- SAFE RESPONSE EXTRACTION (HANDLES ALL FORMATS) ---
            response_text = ""
            
            # --- CASE 1: String response ---
            if isinstance(raw_response, str):
                response_text = raw_response
                
            # --- CASE 2: List response [text, visualizations] ---
            elif isinstance(raw_response, list):
                if len(raw_response) > 0:
                    response_text = str(raw_response[0])
                else:
                    response_text = "Empty list response"
                    
            # --- CASE 3: Tuple response (text, run_id, tool_outputs) ---
            elif isinstance(raw_response, tuple):
                if len(raw_response) > 0:
                    response_text = str(raw_response[0])
                else:
                    response_text = "Empty tuple response"
                    
            # --- CASE 4: Other types ---
            else:
                response_text = str(raw_response)
                
            print(f"📄 Extracted response length: {len(response_text)} chars")
        
            # --- Analyze response for expected aspects ---
            aspect_coverage = self.analyze_response_coverage(
                response_text,
                test_scenario["expected_aspects"]
            )
        
            result = {
                "test_id": test_scenario["id"],
                "persona": persona,
                "question": test_scenario["question"],
                "response": response_text[:500] + "..." if len(response_text) > 500 else response_text,
                "response_time": round(response_time, 2),
                "aspect_coverage": aspect_coverage,
                "expected_aspects": test_scenario["expected_aspects"],
                "covered_aspects": self.get_covered_aspects(response_text, test_scenario["expected_aspects"]),
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }
        
            self.test_log.append({
                "type": "info",
                "message": f"✅ Test {test_scenario['id']} completed in {response_time:.1f}s"
            })
        
            return result
        
        except Exception as e:
            error_msg = f"Test execution failed: {str(e)}\n{traceback.format_exc()}"
            print(f"❌ {error_msg}")
            error_result = self._create_error_result(test_scenario, persona, error_msg)
            self.test_log.append({
                "type": "error",
                "message": f"❌ Test {test_scenario['id']} failed: {str(e)}"
            })
            return error_result
    
    def _create_error_result(self, test_scenario, persona, error_msg):
        """Create error result for failed tests"""
        return {
            "test_id": test_scenario["id"],
            "persona": persona,
            "question": test_scenario["question"],
            "response": f"ERROR: {error_msg[:200]}",
            "response_time": 0,
            "aspect_coverage": 0,
            "expected_aspects": test_scenario["expected_aspects"],
            "covered_aspects": [],
            "timestamp": datetime.now().isoformat(),
            "status": "failed"
        }
    
    def analyze_response_coverage(self, response, expected_aspects):
        """
        Analyze how many expected aspects are covered in the response
        """
        print(f"📊 Analyzing coverage for {len(expected_aspects)} expected aspects")
        
        if not expected_aspects:
            return 0
            
        response_text = str(response).lower()
        covered = 0
        
        # --- Complete keyword matching for aspect coverage ---
        aspect_keywords = {
            "financial": ["cost", "price", "revenue", "profit", "loss", "premium", "deductible", "$", "financial", "budget", "economic", "money"],
            "policy analysis": ["policy", "coverage", "clause", "insurance", "contract", "terms", "agreement", "provision"],
            "risk mitigation": ["mitigation", "prevention", "protection", "safety", "reduction", "defense", "safeguard", "measure"],
            "technical specifications": ["specifications", "technical", "requirements", "standards", "specs", "clearance", "voltage", "kv", "line"],
            "customer impact": ["customer", "resident", "population", "people", "community", "public", "affected", "impact"],
            "safety protocols": ["safety", "protocol", "procedure", "emergency", "evacuation", "alert", "warning", "plan"],
            "claims process": ["claim", "process", "documentation", "paperwork", "filing", "adjuster", "settlement"],
            "coverage details": ["coverage", "details", "limits", "exclusions", "inclusions", "policy", "scope"],
            "financial calculation": ["calculation", "compute", "estimate", "percentage", "amount", "sum", "total", "figure"],
            "risk assessment": ["risk", "assessment", "evaluation", "analysis", "appraisal", "estimate", "rating"],
            "cost analysis": ["cost", "analysis", "benefit", "expense", "price", "value", "investment", "return"],
            "operational decision": ["operational", "decision", "choice", "option", "strategy", "plan", "action"],
            "route planning": ["route", "planning", "path", "road", "highway", "alternate", "detour", "diversion"],
            "timeline impact": ["timeline", "schedule", "delay", "time", "duration", "period", "schedule", "deadline"],
            "inventory management": ["inventory", "stock", "goods", "products", "items", "storage", "warehouse"],
            "logistical planning": ["logistical", "planning", "coordination", "arrangement", "organization", "logistics"],
            "building codes": ["building", "code", "regulation", "standard", "requirement", "compliance", "fireproof"],
            "material costs": ["material", "cost", "price", "expense", "budget", "estimate", "quotation"],
            "compliance": ["compliance", "regulation", "law", "standard", "requirement", "code", "legal"],
            "financial impact": ["financial", "impact", "effect", "consequence", "result", "outcome", "revenue"],
            "contract law": ["contract", "law", "legal", "agreement", "clause", "terms", "liability"],
            "communication": ["communication", "message", "alert", "warning", "notice", "information", "announcement"],
            "visitor management": ["visitor", "tourist", "guest", "public", "people", "management", "safety"]
        }
        
        for aspect in expected_aspects:
            if aspect in aspect_keywords:
                keywords = aspect_keywords[aspect]
                if any(keyword in response_text for keyword in keywords):
                    covered += 1
                    print(f"   ✅ Covered: {aspect}")
                else:
                    print(f"   ❌ Missed: {aspect}")
            else:
                # --- Check if aspect name appears in response ---
                aspect_lower = aspect.lower()
                if aspect_lower in response_text:
                    covered += 1
                    print(f"   ✅ Covered (direct): {aspect}")
                else:
                    print(f"   ❌ Missed (no keywords): {aspect}")
        
        coverage_percent = round(covered / len(expected_aspects) * 100, 1) if expected_aspects else 0
        print(f"📈 Coverage: {covered}/{len(expected_aspects)} = {coverage_percent}%")
        return coverage_percent
    
    def get_covered_aspects(self, response, expected_aspects):
        """
        Get list of actually covered aspects
        """
        response_text = str(response).lower()
        covered = []
        
        aspect_keywords = {
            "financial estimates": ["$", "cost", "price", "revenue", "profit", "loss", "estimate", "calculation", "budget"],
            "policy analysis": ["policy", "coverage", "insurance", "clause", "terms", "agreement"],
            "risk mitigation": ["mitigation", "reduction", "prevention", "protection", "safeguard"],
            "technical specifications": ["specification", "technical", "requirement", "standard", "voltage", "clearance"],
            "customer impact": ["customer", "resident", "public", "people", "community", "affected"],
            "safety protocols": ["safety", "protocol", "procedure", "emergency", "evacuation", "plan"],
            "claims process": ["claim", "process", "documentation", "filing", "adjuster"],
            "coverage details": ["coverage", "detail", "limit", "exclusion", "inclusion"],
            "financial calculation": ["calculate", "compute", "percentage", "amount", "total"],
            "risk assessment": ["risk", "assessment", "evaluation", "analysis", "appraisal"],
            "cost analysis": ["cost", "analysis", "benefit", "expense", "value"],
            "operational decision": ["operational", "decision", "choice", "option", "strategy"],
            "route planning": ["route", "planning", "path", "alternate", "detour"],
            "timeline impact": ["timeline", "schedule", "delay", "time", "duration"],
            "inventory management": ["inventory", "stock", "goods", "storage", "warehouse"],
            "insurance": ["insurance", "coverage", "policy", "claim", "premium"],
            "logistical planning": ["logistical", "planning", "coordination", "organization"],
            "building codes": ["building", "code", "regulation", "standard", "fireproof"],
            "material costs": ["material", "cost", "price", "budget", "estimate"],
            "compliance": ["compliance", "regulation", "law", "requirement", "standard"],
            "financial impact": ["financial", "impact", "effect", "consequence", "revenue"],
            "contract law": ["contract", "law", "legal", "agreement", "clause"],
            "communication": ["communication", "message", "alert", "warning", "notice"],
            "visitor management": ["visitor", "tourist", "guest", "management", "safety"]
        }
        
        for aspect in expected_aspects:
            if aspect in aspect_keywords:
                keywords = aspect_keywords[aspect]
                if any(keyword in response_text for keyword in keywords):
                    covered.append(aspect)
            else:
                # --- Check direct match ---
                if aspect.lower() in response_text:
                    covered.append(aspect)
        
        return covered
    
    def run_all_tests(self):
        """
        Run all test scenarios
        """
        print("🚀 Starting comprehensive test run...")
        all_scenarios = get_all_scenarios()
        self.results = []
        
        print(f"📋 Total scenarios: {len(all_scenarios)}")
        
        for idx, scenario in enumerate(all_scenarios, 1):
            print(f"\n🔬 Test {idx}/{len(all_scenarios)}: {scenario['persona']} - {scenario['id']}")
            # --- Capture the returned result and store it ---
            result = self.run_single_test(
                scenario["persona"],
                {
                    "id": scenario["id"],
                    "question": scenario["question"],
                    "expected_aspects": scenario["expected_aspects"]
                }
            )
            self.results.append(result)  # --- Store the returned result ---
            time.sleep(1)  # --- Rate limiting ---
        
        print(f"\n✅ All tests completed: {len(self.results)} results")
        return self.results
    
    def run_persona_tests(self, persona):
        """
        Run tests for a specific persona - USING get_test_scenario() 
        """
        print(f"👤 Running tests for persona: {persona}")
        scenarios = get_test_scenario(persona)
        if not scenarios:
            print(f"⚠️ No test scenarios found for {persona}")
            return []
        
        print(f"📊 Found {len(scenarios)} scenarios for {persona}")
        results = []
        for scenario in scenarios:
            result = self.run_single_test(persona, scenario)
            results.append(result)
        
        return results
    
    def run_specific_test(self, persona, scenario_id):
        """
        Run a specific test scenario by ID - USING get_test_scenario() with scenario_id
        """
        print(f"🎯 Running specific test: {persona} - {scenario_id}")
        scenarios = get_test_scenario(persona, scenario_id)
        if not scenarios:
            print(f"⚠️ Scenario {scenario_id} not found for {persona}")
            return None
        
        return self.run_single_test(persona, scenarios[0])
    
    def generate_report(self, results=None):
        """
        Generate test report - FIXED to use provided results or self.results
        """
        print("📄 Generating test report...")
        
        # --- Use provided results if available, otherwise use self.results ---
        if results is not None:
            report_results = results
        else:
            report_results = self.results
            
        if not report_results:
            print("⚠️ No test results available for report")
            # --- Return a default report file path instead of just a string ---
            report_dir = "test_reports"
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            
            report_file = os.path.join(report_dir, f"test_report_empty_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            # --- Create an empty report ---
            report = {
                "summary": {
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 0,
                    "success_rate": 0,
                    "average_coverage": 0,
                    "average_response_time": 0
                },
                "by_persona": {},
                "detailed_results": [],
                "test_log": self.test_log,
                "generated_at": datetime.now().isoformat()
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Empty report saved to: {report_file}")
            return report, report_file
        
        df = pd.DataFrame(report_results)
        
        # --- Calculate metrics ---
        total_tests = len(df)
        passed_tests = len(df[df['status'] == 'completed'])
        failed_tests = total_tests - passed_tests
        avg_coverage = df['aspect_coverage'].mean() if 'aspect_coverage' in df.columns else 0
        avg_response_time = df['response_time'].mean() if 'response_time' in df.columns else 0
        
        # --- Group by persona ---
        persona_stats = {}
        if 'persona' in df.columns:
            persona_stats = df.groupby('persona').agg({
                'aspect_coverage': 'mean',
                'response_time': 'mean',
                'test_id': 'count'
            }).round(2).to_dict()
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": round((passed_tests / total_tests) * 100, 1) if total_tests > 0 else 0,
                "average_coverage": round(avg_coverage, 1),
                "average_response_time": round(avg_response_time, 2)
            },
            "by_persona": persona_stats,
            "detailed_results": report_results,
            "test_log": self.test_log,
            "generated_at": datetime.now().isoformat()
        }
        
        # --- Save report ---
        report_dir = "test_reports"
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        
        report_file = os.path.join(report_dir, f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Report saved to: {report_file}")
        return report, report_file
    
    def display_results(self):
        """
        Display test results in Streamlit
        """
        if not self.results:
            st.warning("No test results to display. Run tests first.")
            return
        
        df = pd.DataFrame(self.results)
        
        st.subheader("📊 Test Results Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tests", len(df))
        with col2:
            passed = len(df[df['status'] == 'completed'])
            st.metric("Passed", passed)
        with col3:
            avg_cov = df['aspect_coverage'].mean()
            st.metric("Avg. Coverage", f"{avg_cov:.1f}%")
        with col4:
            avg_time = df['response_time'].mean()
            st.metric("Avg. Time", f"{avg_time:.1f}s")
        
        st.divider()
        
        # --- Results table ---
        st.subheader("Detailed Results")
        display_df = df[['persona', 'test_id', 'aspect_coverage', 'response_time', 'status']].copy()
        display_df['aspect_coverage'] = display_df['aspect_coverage'].apply(lambda x: f"{x}%")
        display_df['response_time'] = display_df['response_time'].apply(lambda x: f"{x}s")
        
        st.dataframe(display_df, use_container_width=True)
        
        # --- Persona performance ---
        if 'persona' in df.columns:
            st.subheader("Performance by Persona")
            persona_perf = df.groupby('persona')['aspect_coverage'].mean().sort_values(ascending=False)
            if not persona_perf.empty:
                st.bar_chart(persona_perf)