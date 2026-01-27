import os
import argparse
import subprocess

def run_all_evaluations(model_name=None):
    # 1. Get all subfolders in the 'cases' directory
    cases_dir = 'cases'
    if not os.path.exists(cases_dir):
        print(f"❌ Error: '{cases_dir}' directory not found.")
        return

    # Get a list of all folders in 'cases'
    subfolders = [f.path for f in os.scandir(cases_dir) if f.is_dir()]
    
    print(f"🔎 Found {len(subfolders)} cases to evaluate: {[os.path.basename(s) for s in subfolders]}")
    print("-" * 50)

    # 2. Loop through each folder and run the evaluation script
    for folder in subfolders:
        folder_name = os.path.basename(folder)
        print(f"\n🚀 Starting evaluation for: {folder_name}")
        
        # Check if interaction.jsonl exists (skip if empty folder)
        if not os.path.exists(os.path.join(folder, 'interaction.jsonl')):
            print(f"⚠️  Skipping {folder_name}: interaction.jsonl missing.")
            continue

        # Build the command
        cmd = ["python", "src/evaluation/eval_offline.py", "--case_folder", folder]
        if model_name:
            cmd.extend(["--model", model_name])

        # Run it
        try:
            subprocess.run(cmd, check=True)
            print(f"✅ Completed: {folder_name}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed: {folder_name}")
        except Exception as e:
            print(f"❌ Error running script: {e}")

    print("\n🎉 All evaluations finished!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='Optional: Override LLM model name')
    args = parser.parse_args()
    
    run_all_evaluations(args.model)