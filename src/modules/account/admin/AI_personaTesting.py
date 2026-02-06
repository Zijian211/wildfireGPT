import streamlit as st
import pandas as pd
import os
from src.modules.test_scenarios.test_runner import PersonaTestRunner
from src.modules.test_scenarios.test_cases import get_all_scenarios, get_test_scenario
from src.modules.ui.context_manager import PERSONA_PROMPTS
import subprocess
import sys

def render_ai_persona_testing_tab():
    """
    AI Persona Testing Tab
    """
    st.subheader("🧪 AI Persona Testing Suite")
    st.info("Run systematic tests of different personas with predefined scenarios.")
    
    # --- Initialize Test Runner ---
    if 'test_runner' not in st.session_state:
        st.session_state.test_runner = PersonaTestRunner()
    
    # --- Test Configuration ---
    col1, col2 = st.columns(2)
    
    with col1:
        test_mode = st.selectbox(
            "Test Mode",
            ["Quick Test (Single Persona)", "Comprehensive Test (All Personas)", "Specific Scenario"]
        )
    
    with col2:
        if test_mode == "Quick Test (Single Persona)":
            selected_persona = st.selectbox(
                "Select Persona",
                ["👨‍🚒 Emergency Commander (Gov)", "🛡️ Insurance Risk Assessor", "⚡ Power Grid Operator", 
                 "🚚 Logistics Manager", "🏗️ Real Estate Developer", "🏞️ Park Ranger / Tourism"]
            )
        elif test_mode == "Specific Scenario":
            all_scenarios = get_all_scenarios()
            scenario_options = [f"{s['persona']} - {s['id']}: {s['question'][:50]}..." for s in all_scenarios]
            selected_scenario = st.selectbox("Select Scenario", scenario_options)
    
    # --- Display Persona Information ---
    st.markdown("---")
    st.subheader("📋 Persona System Prompts")
    
    persona_cols = st.columns(3)
    persona_list = list(PERSONA_PROMPTS.keys())
    
    for idx, persona in enumerate(persona_list[:6]):  # --- Show first 6 personas ---
        with persona_cols[idx % 3]:
            with st.expander(f"{persona.split(' ')[0]}", expanded=False):
                prompt = PERSONA_PROMPTS[persona]
                if "Focus on:" in prompt:
                    focus_start = prompt.find("Focus on:") + 10
                    focus_end = prompt.find("\n\nDO:", focus_start) if "\n\nDO:" in prompt else len(prompt)
                    focus_text = prompt[focus_start:focus_end]
                    
                    st.markdown("**Focus Areas:**")
                    lines = [line.strip() for line in focus_text.split('\n') if line.strip()]
                    for line in lines[:3]:  # --- Show first 3 focus areas ---
                        if line and (line[0].isdigit() or line.startswith('1.')):
                            point = line[3:] if line[0].isdigit() else line[2:]
                            st.markdown(f"• {point[:50]}...")
                
                # --- Show test count for this persona ---
                scenarios = get_test_scenario(persona)
                if scenarios:
                    st.caption(f"{len(scenarios)} test scenarios available")
    
    # --- Run Tests ---
    st.markdown("---")
    st.subheader("🚀 Run Tests")
    
    if st.button("▶️ Execute Tests", type="primary", use_container_width=True):
        with st.spinner("Running AI persona tests... This may take 2-3 minutes."):
            try:
                if test_mode == "Quick Test (Single Persona)":
                    # --- Run tests for single persona ---
                    scenarios = get_test_scenario(selected_persona)
                    if not scenarios:
                        st.error(f"No test scenarios found for {selected_persona}")
                    else:
                        results = []
                        for scenario in scenarios:
                            result = st.session_state.test_runner.run_single_test(
                                selected_persona,
                                scenario
                            )
                            results.append(result)
                    
                        # --- Store results ---
                        st.session_state.test_results = results
                    
                        # --- Generate report with the actual results ---
                        st.session_state.test_report, st.session_state.report_file = st.session_state.test_runner.generate_report(results)
                        st.success(f"✅ Tests completed for {selected_persona}!")
                    
                elif test_mode == "Comprehensive Test (All Personas)":
                    # --- Run all tests ---
                    results = st.session_state.test_runner.run_all_tests()
                    st.session_state.test_results = results
                
                    # --- Generate report with the actual results ---
                    st.session_state.test_report, st.session_state.report_file = st.session_state.test_runner.generate_report(results)
                    st.success(f"✅ All persona tests completed! Generated report.")
            
                elif test_mode == "Specific Scenario":
                    # --- Parse scenario selection ---
                    scenario_idx = scenario_options.index(selected_scenario)
                    all_scenarios = get_all_scenarios()
                    selected_scenario_data = all_scenarios[scenario_idx]
                
                    result = st.session_state.test_runner.run_single_test(
                        selected_scenario_data["persona"],
                        {
                            "id": selected_scenario_data["id"],
                            "question": selected_scenario_data["question"],
                            "expected_aspects": selected_scenario_data["expected_aspects"]
                        }
                    )
                    st.session_state.test_results = [result]
                
                    # --- Generate report with the actual result ---
                    st.session_state.test_report, st.session_state.report_file = st.session_state.test_runner.generate_report([result])
                    st.success(f"✅ Scenario test completed!")
        
            except Exception as e:
                st.error(f"❌ Test execution failed: {str(e)}")
                st.code(str(e), language="python")
    
    # --- Display Results ---
    if 'test_results' in st.session_state and st.session_state.test_results:
        st.markdown("---")
        st.subheader("📊 Test Results")
        
        # --- Summary Metrics ---
        results_df = pd.DataFrame(st.session_state.test_results)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tests", len(results_df))
        with col2:
            passed = len(results_df[results_df['status'] == 'completed'])
            st.metric("Passed", passed)
        with col3:
            avg_cov = results_df['aspect_coverage'].mean()
            st.metric("Avg. Coverage", f"{avg_cov:.1f}%")
        with col4:
            avg_time = results_df['response_time'].mean()
            st.metric("Avg. Time", f"{avg_time:.1f}s")
        
        # --- Detailed Results ---
        st.subheader("Detailed Results")
        
        # --- Group by persona ---
        if 'persona' in results_df.columns:
            persona_perf = results_df.groupby('persona').agg({
                'aspect_coverage': 'mean',
                'response_time': 'mean',
                'test_id': 'count'
            }).round(2)
            
            st.markdown("**Performance by Persona:**")
            st.dataframe(persona_perf, use_container_width=True)
        
        # --- Individual Test Results ---
        st.markdown("**Individual Test Results:**")
        for idx, result in enumerate(st.session_state.test_results):
            with st.expander(f"{result.get('test_id', 'Test')} - {result.get('persona', 'Unknown')}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Coverage", f"{result.get('aspect_coverage', 0)}%")
                    st.metric("Response Time", f"{result.get('response_time', 0)}s")
                with col_b:
                    st.markdown("**Question:**")
                    st.info(result.get('question', 'No question'))
                    st.markdown("**Covered Aspects:**")
                    st.write(", ".join(result.get('covered_aspects', [])))
                
                st.markdown("**Response Preview:**")
                result_index = st.session_state.test_results.index(result)
                st.text_area("AI Response", result.get('response', 'No response'), height=150, key=f"resp_{idx}")
        
        # --- Download Report ---
        # --- Check if report_file exists and is not None ---
        if 'report_file' in st.session_state and st.session_state.report_file:
            report_file_path = st.session_state.report_file
            # --- Check if it's a valid path string ---
            if isinstance(report_file_path, str) and os.path.exists(report_file_path):
                with open(report_file_path, 'rb') as f:
                    st.download_button(
                        label="📥 Download Full Test Report",
                        data=f,
                        file_name=os.path.basename(report_file_path),
                        mime="application/json",
                        use_container_width=True
                    )
            else:
                st.warning(f"Report file not found: {report_file_path}")
    
    # --- Command Line Interface ---
    st.markdown("---")
    st.subheader("🖥️ Backend Test Execution")
    st.info("Run tests directly from command line for batch processing.")
    
    code = """# Run all persona tests
python run_tests.py --persona all --output test_report.json

# Run tests for specific persona
python run_tests.py --persona "🛡️ Insurance Risk Assessor" --output insurance_tests.json

# Run with verbose output
python run_tests.py --persona all --verbose"""
    
    st.code(code, language="bash")
    
    # --- Quick command generator for users ---
    st.markdown("**Generate Command:**")
    gen_persona = st.selectbox("Select Persona for CLI", 
                              ["all", "👨‍🚒 Emergency Commander (Gov)", "🛡️ Insurance Risk Assessor", 
                               "⚡ Power Grid Operator", "🚚 Logistics Manager", 
                               "🏗️ Real Estate Developer", "🏞️ Park Ranger / Tourism"])
    
    output_file = st.text_input("Output file name", "test_results.json")
    
    if st.button("📋 Copy Command"):
        cmd = f"python run_tests.py --persona \"{gen_persona}\" --output {output_file}"
        st.code(cmd, language="bash")
        st.success("Command copied to clipboard (simulated)")