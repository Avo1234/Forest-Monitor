import sys
import sentinel

def main():
    print("==================================================")
    print("Starting Weekly SAR Deforestation Detection Pipeline")
    print("==================================================")
    try:
        sentinel.run_weekly_deforestation_job()
        print("Pipeline execution completed successfully.")
    except Exception as e:
        print(f"Pipeline failed with error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
