import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import styles from './index.module.css';

function Hero() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={styles.hero}>
      <div className="container">
        <Heading as="h1">{siteConfig.title}</Heading>
        <p className={styles.tagline}>{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link className="button button--primary button--lg" to="/docs/quickstart">
            Get Started →
          </Link>
          <Link
            className="button button--secondary button--lg"
            href="https://github.com/bardiakhosravi/answer-guard"
          >
            View on GitHub
          </Link>
        </div>
      </div>
    </header>
  );
}

function Feature({ title, description }: { title: string; description: string }) {
  return (
    <div className="col col--4">
      <div className={styles.feature}>
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

const features = [
  {
    title: 'PM-driven quality control',
    description:
      'Let product managers highlight bad agent responses and create enforceable guidelines — no prompt engineering required.',
  },
  {
    title: 'Drop-in SDK integration',
    description:
      'Add runtime Q&A capture to your existing agent pipeline in under 5 lines of code. Python and TypeScript SDKs included.',
  },
  {
    title: 'Historical import from BigQuery',
    description:
      'Already have months of Q&A data in BigQuery? Import it all in minutes and start reviewing from day one.',
  },
];

export default function Home() {
  return (
    <Layout description="Response quality enforcement for AI agent products — open source">
      <Hero />
      <main>
        <section className={styles.features}>
          <div className="container">
            <div className="row">
              {features.map((f) => (
                <Feature key={f.title} {...f} />
              ))}
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
