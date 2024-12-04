import subprocess
import sys
import os

def display_menu():
    """Display the main menu."""
    print("Choose from the following options:")
    print("1) Develop Question Set")
    print("2) Perform Analysis")
    print("3) Generate Reports")
    print("4) Exit")

def main():
    while True:
        display_menu()
        choice = input("Enter your choice (1-4): ").strip()

        if choice == "1":
            print("Running Develop Question Set script...")
            subprocess.run(["python", "question_expectation_feature_v1.py"])  # Replace with actual script path
        elif choice == "2":
            print("Running Perform Analysis script...")
            subprocess.run(["python", "perform_analysis.py"])  # Replace with actual script path
        elif choice == "3":
            print("Running Generate Reports script...")
            subprocess.run(["python", "generate_reports.py"])  # Replace with actual script path
        elif choice == "4":
            print("Exiting. Goodbye!")
            sys.exit()
        else:
            print("Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    main()