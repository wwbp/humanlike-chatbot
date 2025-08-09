#!/usr/bin/env python3
"""
Simplified test runner for the chatbot application.

This script consolidates test execution and provides a clean, focused
testing experience without the complexity of scattered test files.
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line
from django.test.utils import get_runner


def setup_test_environment():
    """Set up the Django test environment."""
    # Add the project directory to Python path
    project_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_dir)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'generic_chatbot.test_settings')
    
    # Configure Django
    django.setup()


def run_tests():
    """Run the consolidated test suite."""
    setup_test_environment()
    
    # Get test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Define test patterns
    test_patterns = [
        'tests.test_core_functionality',  # Main consolidated test file
        'tests.test_config',              # Test configuration
    ]
    
    # Run tests
    failures = test_runner.run_tests(test_patterns)
    
    if failures:
        sys.exit(1)
    else:
        print("\n✅ All tests passed successfully!")
        sys.exit(0)


def run_specific_test(test_name):
    """Run a specific test or test class."""
    setup_test_environment()
    
    # Get test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Run specific test
    test_pattern = f'tests.test_core_functionality.{test_name}'
    failures = test_runner.run_tests([test_pattern])
    
    if failures:
        print(f"\n❌ Test {test_name} failed!")
        sys.exit(1)
    else:
        print(f"\n✅ Test {test_name} passed successfully!")


def run_test_coverage():
    """Run tests with coverage reporting."""
    try:
        import coverage
    except ImportError:
        print("❌ Coverage package not installed. Install with: pip install coverage")
        sys.exit(1)
    
    setup_test_environment()
    
    # Start coverage measurement
    cov = coverage.Coverage()
    cov.start()
    
    # Run tests
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    test_patterns = ['tests.test_core_functionality']
    failures = test_runner.run_tests(test_patterns)
    
    # Stop coverage measurement
    cov.stop()
    cov.save()
    
    # Generate coverage report
    print("\n📊 Coverage Report:")
    cov.report()
    
    # Generate HTML report
    cov.html_report(directory='htmlcov')
    print("\n📁 HTML coverage report generated in 'htmlcov/' directory")
    
    if failures:
        sys.exit(1)
    else:
        print("\n✅ All tests passed with coverage reporting!")
        sys.exit(0)


def main():
    """Main entry point for the test runner."""
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [command]")
        print("\nCommands:")
        print("  all          - Run all tests")
        print("  test <name>  - Run specific test (e.g., TestCoreChatFunctionality)")
        print("  coverage     - Run tests with coverage reporting")
        print("  help         - Show this help message")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'all':
        run_tests()
    elif command == 'test' and len(sys.argv) > 2:
        test_name = sys.argv[2]
        run_specific_test(test_name)
    elif command == 'coverage':
        run_test_coverage()
    elif command == 'help':
        print("Chatbot Test Runner")
        print("==================")
        print("\nThis test runner consolidates all testing into a single, focused approach.")
        print("\nAvailable commands:")
        print("  all          - Run the complete consolidated test suite")
        print("  test <name>  - Run a specific test class or method")
        print("  coverage     - Run tests with detailed coverage reporting")
        print("  help         - Show this help message")
        print("\nExamples:")
        print("  python run_tests.py all")
        print("  python run_tests.py test TestCoreChatFunctionality")
        print("  python run_tests.py test test_run_chat_round_success")
        print("  python run_tests.py coverage")
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'python run_tests.py help' for usage information")
        sys.exit(1)


if __name__ == '__main__':
    main()
