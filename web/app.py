# Copyright (C) 2025 AIDC-AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Pixelle-Video Web UI - Main Entry Point

This is the entry point for the Streamlit multi-page application.
Uses st.navigation to define pages and set the default page to Home.
"""

import sys
import json
from pathlib import Path

_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import streamlit as st
import streamlit.components.v1 as components

from web.i18n import get_language, set_language

# Sync language from session state before anything else
if "language" in st.session_state:
    set_language(st.session_state["language"])

_lang = get_language()
_zh = _lang == "zh_CN"

st.set_page_config(
    page_title="Pixelle-Video - AI 视频生成器" if _zh else "Pixelle-Video - AI Video Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "Pixelle-Video - AI 视频生成器" if _zh else "Pixelle-Video - AI Video Generator",
        "Get Help": "https://github.com/ATH-MaaS/Pixelle-Video/issues",
        "Report a Bug": "https://github.com/ATH-MaaS/Pixelle-Video/issues",
    },
)

# Hide Deploy button
st.markdown("""
    <style>
    [data-testid="stDeployButton"],
    .stDeployButton,
    div[data-testid="stDeployButton-Deployment"],
    button[kind="header"],
    a[href*="deploy"],
    a[href*="streamlit.io/cloud"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# Translate built-in three-dot menu items via JS
_menu_map = {
    "Settings": "设置" if _zh else "Settings",
    "Print": "打印" if _zh else "Print",
    "About": "关于" if _zh else "About",
    "Get help": "获取帮助" if _zh else "Get help",
    "Report a bug": "报告问题" if _zh else "Report a bug",
    "Rerun": "重新运行" if _zh else "Rerun",
    "Record a screencast": "录制屏幕" if _zh else "Record a screencast",
    "Developer options": "开发者选项" if _zh else "Developer options",
}

_js = """
<script>
(function() {
    const translations = %s;

    function translateMenu() {
        // Walk all text nodes in the document
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        const toUpdate = [];
        let node;
        while (node = walker.nextNode()) {
            const text = node.textContent.trim();
            if (translations[text]) {
                toUpdate.push({node, value: translations[text]});
            }
        }
        toUpdate.forEach(({node, value}) => {
            node.textContent = value;
        });
    }

    translateMenu();

    const observer = new MutationObserver(() => {
        translateMenu();
    });
    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
})();
</script>
""" % json.dumps(_menu_map, ensure_ascii=False)

st.html(_js, unsafe_allow_javascript=True)


def main():
    """Main entry point with navigation"""
    zh = get_language() == "zh_CN"

    home_page = st.Page(
        "pages/1_🎬_Home.py",
        title="首页" if zh else "Home",
        icon="🎬",
        default=True
    )

    history_page = st.Page(
        "pages/2_📚_History.py",
        title="历史记录" if zh else "History",
        icon="📚"
    )

    pg = st.navigation([home_page, history_page])
    pg.run()


if __name__ == "__main__":
    main()
