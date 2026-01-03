"""Streamlit UI for AI News Agent System."""

import requests
import streamlit as st
from PIL import Image
from io import BytesIO

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="AI News Agent",
    page_icon="📰",
    layout="wide",
)

# Title and description
st.title("📰 AI News Agent for LinkedIn")
st.markdown(
    "Generate professional LinkedIn posts from the latest AI and talent/hiring news."
)

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    st.info(
        "Make sure the FastAPI server is running:\n\n"
        "```bash\n"
        "uvicorn src.api.server:app --reload\n"
        "```"
    )
    
    # Check API health
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ API is running")
        else:
            st.error("❌ API returned an error")
    except requests.exceptions.RequestException:
        st.error("❌ Cannot connect to API")
        st.stop()

# Main content
tab1, tab2 = st.tabs(["📰 Collect News", "✨ Generate Posts"])

# Tab 1: Collect News
with tab1:
    st.header("Collect News Articles")
    st.markdown("Fetch and filter the latest news about AI in talent/hiring/HR.")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        news_count = st.slider(
            "Number of articles to collect",
            min_value=1,
            max_value=10,
            value=5,
            help="Collects top 10 and filters to this many most relevant articles",
        )
    with col2:
        days = st.slider(
            "Recency window (days)",
            min_value=1,
            max_value=30,
            value=7,
            help="Limit news to the past N days",
        )
    with col3:
        collect_button = st.button("🔍 Collect News", type="primary", width='stretch')
    
    if collect_button:
        with st.spinner("Collecting news articles..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/news/collect",
                    params={"count": news_count, "days": days},
                    timeout=60,
                )
                response.raise_for_status()
                data = response.json()
                
                st.success(f"✅ Collected {data['total_count']} articles. Filtered to {data['filtered_count']}.")

                st.subheader("All Results (Raw)")
                for i, article in enumerate(data.get("all_articles", []), start=1):
                    st.write(f"{i}. [{article['title']}]({article['url']})")

                st.subheader("AI-Filtered Top Results")
                for i, article in enumerate(data.get("filtered_articles", data.get('articles', [])), start=1):
                    with st.expander(f"📄 {i}. {article['title']}", expanded=(i == 1)):
                        col_a, col_b = st.columns([2, 1])
                        with col_a:
                            st.markdown(f"**Summary:** {article.get('summary', 'N/A')}")
                            st.markdown(f"**URL:** [{article['url']}]({article['url']})")
                        with col_b:
                            category = article.get("category", "N/A")
                            st.metric("Category", category.replace("_", " ").title())
                            st.metric("Relevance", f"{article.get('relevance_score', 0):.2f}")
                            if article.get("source"):
                                st.caption(f"Source: {article['source']}")
                
            except requests.exceptions.HTTPError as e:
                st.error(f"❌ API Error: {e.response.text}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Tab 2: Generate Posts
with tab2:
    st.header("Generate LinkedIn Posts")
    st.markdown("Create professional LinkedIn posts with branded images from news articles.")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        post_count = st.slider(
            "Number of posts to generate",
            min_value=1,
            max_value=5,
            value=1,
            help="Generates this many LinkedIn posts with images",
        )
    with col2:
        save_to_disk = st.checkbox(
            "Save to disk",
            value=True,
            help="Save generated posts and images to output/ directory",
        )
    with col3:
        generate_button = st.button("✨ Generate", type="primary", width='stretch')

    st.markdown("### Select URLs to include (optional)")
    selected_urls = st.text_area(
        "Paste article URLs to include (one per line). If empty, filtered articles will be used.",
        value="",
        placeholder="https://example.com/article-1\nhttps://example.com/article-2",
        height=120,
    )
    extra_urls = st.text_input(
        "Add any additional URL (optional)",
        value="",
        placeholder="https://example.com/another-article",
    )

    live = st.checkbox("Live updates (progressive)", value=False, help="Show items as they complete (uses async job)")

    if generate_button and not live:
        with st.spinner(f"Generating {post_count} post(s) with images... This may take a minute."):
            try:
                urls_list = [u.strip() for u in selected_urls.splitlines() if u.strip()]
                extra_list = [extra_urls.strip()] if extra_urls.strip() else []
                payload = {
                    "count": post_count,
                    "days": 7,
                    "save_to_disk": save_to_disk,
                    "selected_urls": urls_list,
                    "extra_urls": extra_list,
                }
                response = requests.post(f"{API_BASE_URL}/api/generate", json=payload, timeout=180)
                response.raise_for_status()
                generated_content = response.json()
                
                st.success(f"✅ Generated {len(generated_content)} post(s) with images!")
                
                # Display generated content
                for item in generated_content:
                    post_index = item["post_index"]
                    post = item["post"]
                    image_data = item["image"]
                    
                    st.divider()
                    st.subheader(f"📝 Post #{post_index}")
                    
                    # Two columns: post content and image
                    col_post, col_image = st.columns([1, 1])
                    
                    with col_post:
                        st.markdown("**Content:**")
                        st.write(post["content"])
                        
                        st.markdown("**Hashtags:**")
                        hashtags = " ".join([f"#{tag}" for tag in post.get("hashtags", [])])
                        st.code(hashtags, language=None)
                        
                        st.markdown("**Source:**")
                        st.caption(f"{post.get('news_article_title', 'N/A')}")
                        if post.get("news_article_url"):
                            st.caption(f"[Read article]({post['news_article_url']})")
                    
                    with col_image:
                        st.markdown("**Generated Image:**")
                        
                        # Try to display image
                        image_url = image_data.get("image_url")
                        image_path = image_data.get("image_path")
                        
                        if image_path:
                            try:
                                img = Image.open(image_path)
                                st.image(img, width='stretch')
                            except Exception:
                                if image_url:
                                    st.image(image_url, width='stretch')
                        elif image_url:
                            st.image(image_url, width='stretch')
                        else:
                            st.warning("No image available")
                        
                        if save_to_disk and image_path:
                            st.caption(f"💾 Saved to: `{image_path}`")
                
            except requests.exceptions.HTTPError as e:
                st.error(f"❌ API Error: {e.response.text}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    elif generate_button and live:
        try:
            urls_list = [u.strip() for u in selected_urls.splitlines() if u.strip()]
            extra_list = [extra_urls.strip()] if extra_urls.strip() else []
            payload = {
                "count": post_count,
                "days": 7,
                "save_to_disk": save_to_disk,
                "selected_urls": urls_list,
                "extra_urls": extra_list,
            }
            job_resp = requests.post(f"{API_BASE_URL}/api/generate/async", json=payload, timeout=30)
            job_resp.raise_for_status()
            job = job_resp.json()
            job_id = job["job_id"]
            total = job["total_expected"]
            st.success(f"Job started: {job_id} (expecting {total} items)")

            placeholder = st.empty()
            seen = 0

            import time
            while True:
                status_resp = requests.get(f"{API_BASE_URL}/api/generate/status/{job_id}", timeout=30)
                if status_resp.status_code == 404:
                    st.error("Job not found")
                    break
                status = status_resp.json()
                items = status.get("items", [])

                with placeholder.container():
                    st.subheader(f"Progress: {status['completed']}/{status['total_expected']}")
                    for item in items:
                        post = item["post"]
                        image_data = item["image"]
                        st.divider()
                        st.subheader(f"📝 Post #{item['post_index']}")
                        col_post, col_image = st.columns([1, 1])
                        with col_post:
                            st.write(post["content"])
                            hashtags = " ".join([f"#{tag}" for tag in post.get("hashtags", [])])
                            st.code(hashtags, language=None)
                            st.caption(f"{post.get('news_article_title', 'N/A')}")
                            if post.get("news_article_url"):
                                st.caption(f"[Read article]({post['news_article_url']})")
                        with col_image:
                            image_url = image_data.get("image_url")
                            image_path = image_data.get("image_path")
                            if image_path:
                                try:
                                    img = Image.open(image_path)
                                    st.image(img, width='stretch')
                                except Exception:
                                    if image_url:
                                        st.image(image_url, width='stretch')
                            elif image_url:
                                st.image(image_url, width='stretch')
                            else:
                                st.warning("No image available yet")
                    if status["completed"] >= status["total_expected"]:
                        st.success("✅ Job completed")
                        break
                time.sleep(2)
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ API Error: {e.response.text}")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Footer
st.divider()
st.caption("AI News Agent System | Built with FastAPI, Pydantic AI, and Streamlit")

