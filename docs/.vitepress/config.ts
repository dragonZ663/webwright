import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid({
  title: 'Webwright 文档',
  description: 'Webwright 源码分析与学习笔记',
  lang: 'zh-CN',
  cleanUrls: true,
  ignoreDeadLinks: true,

  head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }],
    ['style', {}, `
      :root {
        --vp-layout-max-width: 1600px;
      }
      .content-container {
        max-width: 1000px !important;
      }
      .vp-doc pre code {
        white-space: pre-wrap;
        overflow-wrap: break-word;
      }
    `],
  ],

  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: 'GitHub', link: 'https://github.com/microsoft/Webwright' },
    ],

    sidebar: [
      {
        text: '📖 Webwright 入门',
        collapsed: false,
        items: [
          { text: '框架总览', link: '/webwright浅析' },
        ],
      },
      {
        text: '🏗️ 架构分析',
        collapsed: false,
        items: [
          { text: '配置文件系统', link: '/config_analysis' },
          { text: '两种环境模式对比', link: '/workspace_vs_browser_mode' },
          { text: 'pyproject.toml 配置分析', link: '/pyproject_analysis' },
          { text: 'base.yaml 提示词翻译', link: '/base_prompts_zh' },
        ],
      },
      {
        text: '🔧 功能模块',
        collapsed: false,
        items: [
          { text: 'AI 自动化测试分析', link: '/ai_automation_testing_analysis' },
          { text: 'Image QA & Self Reflection', link: '/image_qa_and_self_reflection' },
        ],
      },
      {
        text: '📚 参考资料',
        collapsed: false,
        items: [
          { text: 'Shell 命令速查', link: '/shell_quickref' },
          { text: 'Python 打包解析', link: '/python_packaging_explained' },
        ],
      },
    ],

    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索文档' },
          modal: { noResultsText: '没有找到相关内容' },
        },
      },
    },

    outline: { level: [2, 3], label: '目录' },
    docFooter: { prev: '上一篇', next: '下一篇' },
    lastUpdated: { text: '最后更新' },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/microsoft/Webwright' },
    ],

    footer: {
      message: '基于 Webwright 源码分析整理',
      copyright: `© ${new Date().getFullYear()} Webwright Docs`,
    },
  },
})
