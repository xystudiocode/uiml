import { withMermaid } from "vitepress-plugin-mermaid";

export default withMermaid({
  base: '/uiml/',
  head: [['link', { rel: 'icon', href: '/imgs/logo.png' }]],
  markdown: {
    emoji: {
      enabled: 'off',
    },
  },

  // 主题配置
  themeConfig: {
    logo: '/imgs/logo.png',
    siteTitle: 'Uiml docs',

    // 搜索功能
    search: {
      provider: 'local',
      options: {
        locales: {
          'zh-CN': {
            translations: {
              button: {
                buttonText: '搜索',
                buttonAriaLabel: '搜索',
              },
              modal: {
                noResultsText: '无法找到相关结果',
                resetButtonTitle: '清除查询条件',
                footer: {
                  selectText: '选择',
                  navigateText: '切换',
                  closeText: '关闭',
                },
              },
            },
          },
          en: {
            translations: {
              button: {
                buttonText: 'Search',
                buttonAriaLabel: 'Search',
              },
              modal: {
                noResultsText: 'No results found',
                resetButtonTitle: 'Clear query',
                footer: {
                  selectText: 'to select',
                  navigateText: 'to navigate',
                  closeText: 'to close',
                },
              },
            },
          },
        },
      },
    },
  },

  // 多语言配置
  locales: {
    en: {
      title: 'Uiml docs',
      description: 'Uiml docs powered by vitepress',
      label: 'English',
      lang: 'en',
      link: '/en/',
      themeConfig: {
        outlineTitle: 'On this page',
        lastUpdatedText: 'Last Updated',
        editLink: {
          pattern:
            'https://github.com/xystudiocode/uiml/tree/main/document/docs/:path',
          text: 'Edit this page',
        },
        docFooter: {
          prev: 'Previous',
          next: 'Next',
        },
        notFound: {
          title: 'PAGE NOT FOUND',
          quote:
            "But if you don't change your direction, and if you keep looking, you may end up where you are heading.",
          linkText: 'Take me home',
        },
        // 配置主题
        lightModeSwitchTitle: 'Switch to light mode',
        darkModeSwitchTitle: 'Switch to dark mode',
        // 社交链接
        socialLinks: [
          { icon: 'github', link: 'https://github.com/xystudiocode/uiml/' },
        ],
        returnToTopLabel: 'Return to top',
        nav: [
          { text: 'Home', link: '/en/'},
          { text: 'Code Library Usage', link: '/en/code/'}
        ],
        sidebar: {
          '/en/code': [
            {
              text: 'Code Library Usage',
              items: [
                { text: 'Index', link: '/en/code/' },
                { text: 'Getting Started', link: '/en/code/getting-started' },
                { text: 'Parameter Meaning', link: '/en/code/value' },
                { text: 'Customization', link: '/en/code/custom' }
              ]
            }
          ]
      },
      },
    },
    'zh-CN': {
      label: '简体中文',
      description: '基于 vitepress 搭建的 Uiml 文档',
      title: 'Uiml 文档 | VitePress',
      link: '/zh-CN/',
      lang: 'zh-CN',
      themeConfig: {
        siteTitle: 'Uiml 文档',
        returnToTopLabel: '返回顶部',
        outlineTitle: '本页目录',
        lastUpdatedText: '最后更新',
        sidebarMenuLabel: '目录',
        editLink: {
          pattern:
            'https://github.com/xystudiocode/uiml/tree/main/document/docs/:path',
          text: '编辑此页',
        },
        notFound: {
          title: '页面不存在',
          quote: '只要不改变你的方向，一直寻找，最终会找到你所寻找的目标',
          linkText: '返回首页',
        },
        // 配置主题
        lightModeSwitchTitle: '切换到浅色模式',
        darkModeSwitchTitle: '切换到深色模式',
        darkModeSwitchLabel: '主题',
        // 社交链接
        socialLinks: [
          { icon: 'github', link: 'https://github.com/xystudiocode/uiml/' },
        ],
        docFooter: {
          prev: '上一页',
          next: '下一页',
        },
        footer: {
          message: '本软件使用MIT协议开源',
          copyright: '© 2025-现在 xystudio版权所有',
        },
        nav: [
          { text: '首页', link: '/zh-CN/'},
          { text: '代码库使用', link: '/zh-CN/code/'}
        ],
        sidebar: {
          '/zh-CN/code': [
            {
              text: '代码库使用',
              items: [
                { text: '目录', link: '/zh-CN/code/' },
                { text: '开始', link: '/zh-CN/code/getting-started' },
                { text: '参数含义', link: '/zh-CN/code/value' },
                { text: '自定义', link: '/zh-CN/code/custom' }
              ]
            }
          ]
      },
    },
  },
}});
