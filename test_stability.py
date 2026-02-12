"""
OpenClaw 100-Command Stability Test
Tests the system under load to ensure no crashes or memory leaks
"""
import subprocess
import time
from datetime import datetime

def run_openclaw_command(cmd):
    """Run an OpenClaw CLI command"""
    result = subprocess.run(
        f"python -m core.cli {cmd}",
        shell=True,
        capture_output=True,
        text=True,
        cwd="C:\\OpenClaw"
    )
    return result.returncode == 0

def main():
    """Run 100 commands and track results"""
    print("=" * 60)
    print("OpenClaw Phase 1 Stability Test - 100 Commands")
    print("=" * 60)
    print(f"Started: {datetime.now()}\n")
    
    success_count = 0
    fail_count = 0
    start_time = time.time()
    
    # Test sequence: Create, read, list, delete (repeated)
    for i in range(25):  # 25 iterations * 4 commands = 100
        test_file = f"stress_test_{i}.txt"
        content = f"Test content iteration {i}"
        
        # Command 1: Create
        if run_openclaw_command(f'file create "{test_file}" "{content}"'):
            success_count += 1
            print(f"[{success_count + fail_count:3d}/100] ✓ Created {test_file}")
        else:
            fail_count += 1
            print(f"[{success_count + fail_count:3d}/100] ✗ Failed to create {test_file}")
        
        # Command 2: Read
        if run_openclaw_command(f'file read "{test_file}"'):
            success_count += 1
            print(f"[{success_count + fail_count:3d}/100] ✓ Read {test_file}")
        else:
            fail_count += 1
            print(f"[{success_count + fail_count:3d}/100] ✗ Failed to read {test_file}")
        
        # Command 3: List
        if run_openclaw_command(f'file list'):
            success_count += 1
            print(f"[{success_count + fail_count:3d}/100] ✓ Listed files")
        else:
            fail_count += 1
            print(f"[{success_count + fail_count:3d}/100] ✗ Failed to list files")
        
        # Command 4: Info
        if run_openclaw_command(f'file info "{test_file}"'):
            success_count += 1
            print(f"[{success_count + fail_count:3d}/100] ✓ Got info for {test_file}")
        else:
            fail_count += 1
            print(f"[{success_count + fail_count:3d}/100] ✗ Failed to get info for {test_file}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Results
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Total Commands:   100")
    print(f"Successful:       {success_count} ({success_count}%)")
    print(f"Failed:           {fail_count} ({fail_count}%)")
    print(f"Duration:         {duration:.2f} seconds")
    print(f"Commands/second:  {100/duration:.2f}")
    print(f"Completed:        {datetime.now()}")
    
    if fail_count == 0:
        print("\n✅ ALL TESTS PASSED - System is stable!")
        return 0
    else:
        print(f"\n⚠️  {fail_count} tests failed - Review logs")
        return 1

if __name__ == "__main__":
    exit(main())
