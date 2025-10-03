"""Onboarding tab for Streamlit dashboard.

Shows environment variable checklist, validation status, and setup guidance.
"""

import os
from pathlib import Path

import streamlit as st


# Required environment variables
REQUIRED_VARS = {
    "OPENAI_API_KEY": "OpenAI API key for LLM inference",
    "OPENAI_MODEL": "Model to use (e.g., gpt-4o, gpt-4o-mini)",
    "CURRENT_REGION": "Current deployment region (e.g., us-east-1, us-west-2)",
    "TENANT_ID": "Tenant identifier for multi-tenancy",
}

# Optional environment variables with defaults
OPTIONAL_VARS = {
    "OPENAI_BASE_URL": ("https://api.openai.com/v1", "OpenAI API base URL"),
    "OPENAI_MAX_TOKENS": ("2000", "Maximum tokens per request"),
    "OPENAI_TEMPERATURE": ("0.7", "Temperature for generation (0.0-2.0)"),
    "OPENAI_CONNECT_TIMEOUT_MS": ("30000", "Connection timeout in milliseconds"),
    "OPENAI_READ_TIMEOUT_MS": ("60000", "Read timeout in milliseconds"),
    "MAX_RETRIES": ("3", "Maximum retry attempts for API calls"),
    "RETRY_BASE_MS": ("400", "Base retry delay in milliseconds"),
    "RETRY_JITTER_PCT": ("0.2", "Jitter percentage for retries (0.0-1.0)"),
    "FEATURE_MULTI_REGION": ("false", "Enable multi-region deployment"),
}


def validate_env_var(name: str, value: str | None) -> tuple[bool, str | None]:
    """
    Validate an environment variable value.

    Args:
        name: Variable name
        value: Variable value (None if not set)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if value is None or value.strip() == "":
        return False, "Not set"

    # Specific validations
    if name == "OPENAI_API_KEY":
        if not value.startswith("sk-"):
            return False, "Should start with 'sk-'"

    if name == "OPENAI_TEMPERATURE":
        try:
            temp = float(value)
            if temp < 0.0 or temp > 2.0:
                return False, "Should be between 0.0 and 2.0"
        except ValueError:
            return False, "Should be a valid float"

    if name.endswith("_TIMEOUT_MS"):
        try:
            timeout = int(value)
            if timeout <= 0:
                return False, "Should be a positive integer"
        except ValueError:
            return False, "Should be a valid integer"

    if name == "MAX_RETRIES":
        try:
            retries = int(value)
            if retries < 0:
                return False, "Should be a non-negative integer"
        except ValueError:
            return False, "Should be a valid integer"

    if name == "RETRY_JITTER_PCT":
        try:
            jitter = float(value)
            if jitter < 0.0 or jitter > 1.0:
                return False, "Should be between 0.0 and 1.0"
        except ValueError:
            return False, "Should be a valid float"

    return True, None


def render_onboarding_tab():
    """Render onboarding tab with environment validation and setup guidance."""
    st.subheader("🚀 Onboarding & Setup")

    st.markdown(
        """
    Welcome to OpenAI Agents Workflows! This tab helps you validate your environment
    configuration and get started with the system.
    """
    )

    # Required Variables Section
    st.markdown("---")
    st.markdown("### Required Environment Variables")

    all_required_valid = True
    for var_name, description in REQUIRED_VARS.items():
        value = os.getenv(var_name)
        is_valid, error = validate_env_var(var_name, value)

        col1, col2, col3 = st.columns([2, 1, 3])

        with col1:
            st.markdown(f"**{var_name}**")

        with col2:
            if is_valid:
                st.success("✅ Valid")
            else:
                st.error("❌ Invalid")
                all_required_valid = False

        with col3:
            if is_valid:
                # Mask sensitive values
                if "KEY" in var_name or "SECRET" in var_name:
                    display_value = f"{value[:8]}..." if value else ""
                else:
                    display_value = value
                st.caption(f"Value: `{display_value}`")
            else:
                st.caption(f"⚠️ {error}: {description}")

    # Optional Variables Section
    st.markdown("---")
    st.markdown("### Optional Environment Variables")

    with st.expander("Show optional variables", expanded=False):
        for var_name, (default_value, description) in OPTIONAL_VARS.items():
            value = os.getenv(var_name, default_value)
            is_default = os.getenv(var_name) is None
            is_valid, error = validate_env_var(var_name, value)

            col1, col2, col3 = st.columns([2, 1, 3])

            with col1:
                st.markdown(f"**{var_name}**")

            with col2:
                if is_valid:
                    st.success("✅" if not is_default else "📋")
                else:
                    st.warning("⚠️")

            with col3:
                status = "(using default)" if is_default else "(custom)"
                if is_valid:
                    st.caption(f"Value: `{value}` {status}")
                else:
                    st.caption(f"⚠️ {error}: {description}")

    # Status Summary
    st.markdown("---")
    st.markdown("### Configuration Status")

    if all_required_valid:
        st.success("✅ All required variables are configured correctly!")
        st.info("Your environment is ready. You can proceed to run workflows and use the dashboard.")
    else:
        st.error("❌ Some required variables are missing or invalid.")
        st.warning("Please set the missing/invalid variables before proceeding.")

    # Setup Instructions
    st.markdown("---")
    st.markdown("### Setup Instructions")

    tab1, tab2, tab3 = st.tabs(["Quick Start", "Run Wizard", "Manual Setup"])

    with tab1:
        st.markdown(
            """
        **Quick Start Guide:**

        1. **Set Required Variables:**
           ```bash
           export OPENAI_API_KEY="sk-your-key-here"
           export OPENAI_MODEL="gpt-4o"
           export CURRENT_REGION="us-east-1"
           export TENANT_ID="my-tenant"
           ```

        2. **Run Onboarding Wizard:**
           ```bash
           python -m src.onboarding.wizard
           ```

        3. **Test Example Workflows:**
           ```bash
           # Weekly report (mock mode)
           python -m src.workflows.examples.weekly_report_pack --dry-run

           # Meeting brief (mock mode)
           python -m src.workflows.examples.meeting_transcript_brief --dry-run

           # Inbox sweep (mock mode)
           python -m src.workflows.examples.inbox_drive_sweep --dry-run
           ```

        4. **View Results:**
           Check the `artifacts/` directory for generated outputs.
        """
        )

    with tab2:
        st.markdown(
            """
        **Run the Interactive Onboarding Wizard:**

        The wizard will:
        - Validate all environment variables
        - Generate `.env.example` file
        - Optionally create `.env.local` file
        - Provide next steps guidance
        - Log audit events

        **Command:**
        ```bash
        python -m src.onboarding.wizard
        ```

        **Non-interactive mode (for CI/automation):**
        ```bash
        python -m src.onboarding.wizard --non-interactive
        ```
        """
        )

        if st.button("📋 Copy wizard command"):
            st.code("python -m src.onboarding.wizard", language="bash")
            st.success("Command copied! Run this in your terminal.")

    with tab3:
        st.markdown(
            """
        **Manual Configuration:**

        1. **Create `.env.local` file in project root:**
           ```bash
           # Required
           OPENAI_API_KEY=sk-your-key-here
           OPENAI_MODEL=gpt-4o
           CURRENT_REGION=us-east-1
           TENANT_ID=my-tenant

           # Optional (with defaults)
           OPENAI_BASE_URL=https://api.openai.com/v1
           OPENAI_MAX_TOKENS=2000
           OPENAI_TEMPERATURE=0.7
           OPENAI_CONNECT_TIMEOUT_MS=30000
           OPENAI_READ_TIMEOUT_MS=60000
           MAX_RETRIES=3
           RETRY_BASE_MS=400
           RETRY_JITTER_PCT=0.2
           FEATURE_MULTI_REGION=false
           ```

        2. **Load environment variables:**
           ```bash
           # Using dotenv
           set -a; source .env.local; set +a

           # Or export manually
           export OPENAI_API_KEY="sk-..."
           # ... etc
           ```

        3. **Verify configuration:**
           Refresh this page to see updated validation status.
        """
        )

    # Documentation Links
    st.markdown("---")
    st.markdown("### Documentation & Resources")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        **📚 Configuration**
        - Environment variables reference
        - `.env.example` template
        - Security best practices
        """
        )

    with col2:
        st.markdown(
            """
        **🔧 Example Workflows**
        - Weekly report (professional)
        - Meeting brief (academic)
        - Inbox sweep (personal)
        """
        )

    with col3:
        st.markdown(
            """
        **📊 Monitoring**
        - Cost tracking dashboard
        - Observability metrics
        - Audit logs
        """
        )

    # Troubleshooting
    with st.expander("🔍 Troubleshooting", expanded=False):
        st.markdown(
            """
        **Common Issues:**

        1. **"OPENAI_API_KEY not set"**
           - Make sure you've exported the variable in your shell
           - Check that your API key starts with `sk-`
           - Verify the key is valid at platform.openai.com

        2. **"Import error: No module named 'openai'"**
           - Install dependencies: `pip install -r requirements.txt`
           - Or install OpenAI SDK: `pip install openai`

        3. **"Permission denied" on logs directory**
           - Ensure you have write permissions to project directory
           - Try running with appropriate permissions

        4. **Workflow fails with timeout**
           - Increase timeout values in environment
           - Check your network connection
           - Verify OpenAI API status

        5. **Cost tracking not working**
           - Check that `logs/` directory exists and is writable
           - Verify `logs/cost_events.jsonl` file permissions
        """
        )
