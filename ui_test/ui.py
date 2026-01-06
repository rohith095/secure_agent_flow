import streamlit as st
import time
import json
import sys

# Page configuration
st.set_page_config(
    page_title="CrewAI Agent",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'activity_log' not in st.session_state:
    st.session_state.activity_log = []
if 'result' not in st.session_state:
    st.session_state.result = None

# Product options - replace with your actual products
PRODUCTS = ['Product A', 'Product B', 'Product C', 'Product D', 'Product E']


class StreamlitLogger:
    """Custom logger to capture CrewAI output and display it in real-time"""

    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.buffer = []

    def write(self, text):
        if text.strip():
            self.buffer.append(text)
            # Parse and categorize the output
            self.parse_and_display(text)

    def flush(self):
        pass

    def isatty(self):
        """Required method for stdout compatibility"""
        return False

    def fileno(self):
        """Required method for stdout compatibility"""
        return -1

    def readable(self):
        """Required method for stdout compatibility"""
        return False

    def writable(self):
        """Required method for stdout compatibility"""
        return True

    def seekable(self):
        """Required method for stdout compatibility"""
        return False

    def parse_and_display(self, text):
        """Parse CrewAI output and categorize it"""
        text = text.strip()

        # Detect different types of agent activities
        if "Working Agent:" in text or "Agent:" in text:
            self.add_activity("agent_start", text, "🤖")
        elif "Task:" in text:
            self.add_activity("task", text, "📋")
        elif "Using tool:" in text or "Tool:" in text:
            self.add_activity("tool", text, "🔧")
        elif "Thought:" in text or "Thinking:" in text:
            self.add_activity("thought", text, "💭")
        elif "Observation:" in text:
            self.add_activity("observation", text, "👁️")
        elif "Final Answer:" in text or "Answer:" in text:
            self.add_activity("answer", text, "✅")
        elif "Error" in text or "error" in text:
            self.add_activity("error", text, "❌")
        elif text and len(text) > 10:
            self.add_activity("info", text, "ℹ️")

    def add_activity(self, activity_type, message, icon):
        """Add activity to session state and update display"""
        timestamp = time.strftime("%H:%M:%S")
        st.session_state.activity_log.append({
            'type': activity_type,
            'message': message,
            'icon': icon,
            'timestamp': timestamp
        })
        # Update the display
        self.placeholder.markdown(format_activity_log(), unsafe_allow_html=True)


def format_activity_log():
    """Format activity log with color coding and icons"""
    if not st.session_state.activity_log:
        return "👋 Waiting for agent activity..."

    output = []

    for activity in st.session_state.activity_log:
        # Color coding based on activity type
        colors = {
            'agent_start': {'bg': '#ede9fe', 'border': '#7c3aed', 'text': '#5b21b6'},
            'task': {'bg': '#dbeafe', 'border': '#2563eb', 'text': '#1e40af'},
            'tool': {'bg': '#fef3c7', 'border': '#f59e0b', 'text': '#92400e'},
            'thought': {'bg': '#e0e7ff', 'border': '#6366f1', 'text': '#4338ca'},
            'observation': {'bg': '#ddd6fe', 'border': '#8b5cf6', 'text': '#6b21a8'},
            'answer': {'bg': '#dcfce7', 'border': '#16a34a', 'text': '#15803d'},
            'error': {'bg': '#fee2e2', 'border': '#dc2626', 'text': '#991b1b'},
            'info': {'bg': '#f3f4f6', 'border': '#9ca3af', 'text': '#4b5563'}
        }

        color = colors.get(activity['type'], colors['info'])

        # Clean up the message
        message = activity['message'].replace('<', '&lt;').replace('>', '&gt;')

        output.append(f"""
        <p style="background-color: {color['bg']}; 
                    padding: 10px 12px; 
                    margin: 6px 0; 
                    border-radius: 6px; 
                    border-left: 4px solid {color['border']};
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    font-family: monospace; 
                    font-size: 13px;">
            <span style="font-size: 16px;">{activity['icon']}</span>
            <span style="color: {color['text']}; font-weight: 500; line-height: 1.5; white-space: pre-wrap;">{message}</span>
            <br>
            <span style="color: {color['text']}; opacity: 0.6; font-size: 11px;">{activity['timestamp']}</span>
        </p>
        """)

    return "".join(output)


def run_crew_with_logging(prompt, products, log_placeholder):
    """
    Run CrewAI with detailed logging
    This captures ALL internal agent communications
    """
    st.session_state.activity_log = []
    st.session_state.result = None

    # Example simulation - Replace with actual CrewAI code
    logger = StreamlitLogger(log_placeholder)

    # Simulate agent activity with realistic CrewAI output
    logger.write("Working Agent: Product Analyst")
    time.sleep(0.5)

    logger.write(f"Task: Analyze products {products} based on the prompt: {prompt}")
    time.sleep(0.8)

    logger.write("Thought: I need to understand each product's features and compare them")
    time.sleep(0.7)

    logger.write("Using tool: product_research_tool")
    time.sleep(0.5)

    logger.write(f"Observation: Found detailed information about {products[0]}")
    time.sleep(0.6)

    logger.write("Thought: Now I should compare the key features across all products")
    time.sleep(0.7)

    logger.write("Working Agent: Research Specialist")
    time.sleep(0.5)

    logger.write("Task: Deep dive into product specifications")
    time.sleep(0.6)

    logger.write("Using tool: web_search")
    time.sleep(0.5)

    logger.write("Observation: Retrieved market data and customer reviews")
    time.sleep(0.7)

    logger.write("Thought: Based on the analysis, I can now provide recommendations")
    time.sleep(0.6)

    logger.write("Final Answer: Analysis complete with comprehensive product comparison")

    # Return result
    result = {
        "recommendation": f"After analyzing {', '.join(products)}, the best option depends on your specific needs",
        "products_analyzed": products,
        "confidence_score": 0.92,
        "key_findings": [
            "Product compatibility is high",
            "Cost-effectiveness varies by use case",
            "Customer satisfaction ratings are positive"
        ]
    }

    return result


def run_actual_crewai(prompt, products, log_placeholder):
    """
    Integration with actual CrewAI - executes the knowledge-based crew
    """
    st.session_state.activity_log = []
    logger = StreamlitLogger(log_placeholder)

    # Redirect stdout to capture CrewAI's verbose output
    old_stdout = sys.stdout
    sys.stdout = logger

    try:
        # Import the crew from crew_test
        from ui_test.crew_test import crew_inside

        # Execute the crew
        result = crew_inside.kickoff()

        # Format the result for display
        formatted_result = {
            "status": "success",
            "analysis": str(result),
            "products_analyzed": products,
            "prompt": prompt,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        return formatted_result

    except Exception as e:
        logger.write(f"Error: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "products_analyzed": products,
            "prompt": prompt,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    finally:
        # Restore stdout
        sys.stdout = old_stdout


# ==========================
# MAIN UI
# ==========================

st.title("🤖 CrewAI Agent Interface")
st.markdown("See the complete internal workings of your AI agents in real-time")

# Create two columns
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📝 Input Configuration")

    # Prompt input
    prompt = st.text_area(
        "Task Prompt",
        placeholder="Enter your task description here...",
        height=120,
        help="Describe what you want the agents to analyze"
    )

    st.markdown("#### Select Products")

    # Product selection in a 2x2 grid
    prod_col1, prod_col2 = st.columns(2)

    with prod_col1:
        product1 = st.selectbox("Product 1", [""] + PRODUCTS, key="p1")
        product3 = st.selectbox("Product 3", [""] + PRODUCTS, key="p3")

    with prod_col2:
        product2 = st.selectbox("Product 2", [""] + PRODUCTS, key="p2")
        product4 = st.selectbox("Product 4", [""] + PRODUCTS, key="p4")

    st.markdown("---")

    # Submit button
    submit_button = st.button("🚀 Execute Crew", type="primary", use_container_width=True)

    if submit_button:
        products = [product1, product2, product3, product4]

        # Validation
        if not prompt:
            st.error("⚠️ Please enter a task prompt")
        elif "" in products:
            st.error("⚠️ Please select all 4 products")
        else:
            # Clear previous results
            st.session_state.activity_log = []
            st.session_state.result = None

with col2:
    st.subheader("🔄 Live Agent Activity")
    st.markdown("*Real-time view of agent reasoning, tool usage, and communications*")

    # Create placeholder for dynamic updates
    activity_placeholder = st.empty()

    # Show initial state
    activity_placeholder.markdown(format_activity_log(), unsafe_allow_html=True)

# Process after layout is set up
if submit_button and prompt and "" not in [product1, product2, product3, product4]:
    products = [product1, product2, product3, product4]

    with st.spinner("🤖 Agents are working..."):
        # Use the actual CrewAI implementation
        result = run_actual_crewai(prompt, products, activity_placeholder)

        st.session_state.result = result

# Display final result below the columns
if st.session_state.result:
    st.markdown("---")
    st.subheader("📊 Final Result")

    result_col1, result_col2 = st.columns([2, 1])

    with result_col1:
        st.json(st.session_state.result)

    with result_col2:
        st.download_button(
            label="📥 Download Result as JSON",
            data=json.dumps(st.session_state.result, indent=2),
            file_name=f"crew_result_{int(time.time())}.json",
            mime="application/json",
            use_container_width=True
        )

        if st.button("🔄 Clear and Start New", use_container_width=True):
            st.session_state.activity_log = []
            st.session_state.result = None
            st.rerun()

# Footer with instructions
st.markdown("---")
st.success("""
**✅ Live Integration Active!**

- The UI is now connected to the knowledge-based CrewAI agent
- `verbose=True` is enabled to show internal agent thoughts
- Agent uses knowledge sources: AWS IAM Best Practices & Security Compliance
- All agent reasoning, tool calls, and observations appear in real-time!
- Note: Product selection is ignored - the agent analyzes AWS IAM scenarios
""")
