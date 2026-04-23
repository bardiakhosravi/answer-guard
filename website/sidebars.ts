import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docs: [
    { type: 'doc', id: 'intro', label: 'Overview' },
    { type: 'doc', id: 'quickstart', label: 'Quickstart' },
    {
      type: 'category',
      label: 'Desktop App',
      collapsed: false,
      items: ['desktop/index'],
    },
    {
      type: 'category',
      label: 'Integration Guide',
      collapsed: false,
      items: [
        'integration/index',
        'integration/bigquery',
        'integration/historical-import',
        'integration/python-sdk',
        'integration/typescript-sdk',
        'integration/verification',
      ],
    },
    {
      type: 'category',
      label: 'Governance',
      collapsed: false,
      items: ['governance/response-feedback'],
    },
    {
      type: 'category',
      label: 'Reference',
      collapsed: false,
      items: [
        'reference/api',
        'reference/configuration',
      ],
    },
    { type: 'doc', id: 'troubleshooting', label: 'Troubleshooting' },
  ],
};

export default sidebars;
