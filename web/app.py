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
    },
)

# Hide Deploy button + GitHub/Streamlit links in version info, about dialog, and header
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
    [data-testid="stVersionInfo"] a,
    [data-testid="stVersionInfo"] img,
    [data-testid="stAboutDialog"] a,
    [data-testid="stAboutDialog"] img,
    [data-testid="stHeaderLogo"],
    [data-testid="stMainMenu"] a[href*="github.com"],
    [data-testid="stMainMenu"] a[href*="streamlit.io"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# Comprehensive translation map for menu items and dialog texts
if _zh:
    _menu_map = {
        # Menu items
        "Settings": "设置",
        "Print": "打印",
        "About": "关于",
        "Rerun": "重新运行",
        "Record a screencast": "录制屏幕",
        "Clear cache": "清除缓存",
        "Clear caches": "清除缓存",
        "Developer options": "开发者选项",
        "Development": "开发选项",
        # Settings dialog
        "Run on save": "保存时自动运行",
        "Automatically updates the app when the underlying code is updated.": "当底层代码更新时自动刷新应用。",
        "Appearance": "外观",
        "Wide mode": "宽屏模式",
        "Turn on to make this app occupy the entire width of the screen.": "开启后应用将占据整个屏幕宽度。",
        "Choose app theme": "选择应用主题",
        # Clear cache dialog
        "Are you sure you want to clear the app's function caches?": "确定要清除应用的函数缓存吗？",
        "This will remove all cached entries from functions using": "这将移除以下函数的所有缓存数据：",
        "Cancel": "取消",
        # Screencast dialog
        "Cancel screencast": "取消录制",
        "Start recording!": "开始录制！",
        "Stop recording": "停止录制",
        "Also record audio": "同时录制音频",
        "This will record a video with the contents of your screen, so you can easily share what you're seeing with others.": "此功能将录制屏幕内容视频，方便您与他人分享所见内容。",
        "Press `Esc` any time to stop recording.": "随时按 `Esc` 键停止录制。",
        "Preview your video below:": "在下方预览您的视频：",
        "Save video to disk": "保存视频到本地",
        "WebM format": "WebM 格式",
        "This video is encoded in the": "此视频编码格式为",
        # About dialog
        "About": "关于",
        # Script error dialog
        "Script execution error": "脚本执行错误",
        "Try again": "重试",
        "Close": "关闭",
        "Copy": "复制",
        # Other
        "Connecting to Streamlit server": "正在连接 Streamlit 服务器",
        "Connection error": "连接错误",
        "Reconnected to server.": "已重新连接到服务器。",
    }
else:
    _menu_map = {}

_js = """
<script>
(function() {
    const translations = %s;

    function translateText() {
        if (Object.keys(translations).length === 0) return;
        const doc = window.parent.document || document;
        const walker = doc.createTreeWalker(
            doc.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        const toUpdate = [];
        let node;
        while (node = walker.nextNode()) {
            const text = node.textContent.trim();
            if (translations[text]) {
                toUpdate.push({node: node, value: translations[text]});
            }
        }
        toUpdate.forEach(function(item) {
            item.node.textContent = item.value;
        });
    }

    translateText();

    const doc = window.parent.document || document;
    const MutationObserverCtor = doc.defaultView.MutationObserver || window.MutationObserver;
    const observer = new MutationObserverCtor(function() {
        translateText();
    });
    observer.observe(doc.body, { childList: true, subtree: true, characterData: true });
})();
</script>
""" % json.dumps(_menu_map, ensure_ascii=False)

components.html(_js, height=0, width=0)


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
