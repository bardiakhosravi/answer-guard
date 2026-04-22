import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'AnswerGuard',
  tagline: 'Response quality enforcement for AI agent products',
  favicon: 'img/favicon.ico',

  url: 'https://bardiakhosravi.github.io',
  baseUrl: '/answer-guard/',

  organizationName: 'bardiakhosravi',
  projectName: 'answer-guard',
  trailingSlash: false,

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/bardiakhosravi/answer-guard/tree/main/website/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/answerguard-social.png',
    navbar: {
      title: 'AnswerGuard',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docs',
          position: 'left',
          label: 'Docs',
        },
        {
          href: 'https://github.com/bardiakhosravi/answer-guard',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            { label: 'Quickstart', to: '/docs/quickstart' },
            { label: 'Integration Guide', to: '/docs/integration/' },
            { label: 'API Reference', to: '/docs/reference/api' },
          ],
        },
        {
          title: 'Community',
          items: [
            { label: 'GitHub Issues', href: 'https://github.com/bardiakhosravi/answer-guard/issues' },
            { label: 'GitHub Discussions', href: 'https://github.com/bardiakhosravi/answer-guard/discussions' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} AnswerGuard. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash', 'json', 'yaml'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
