/**
 * Railway infrastructure for the MAISON ÉLAN demonstration storefront.
 *
 * Applied with `railway config plan` and `railway config apply`; see docs/deployment.md.
 * Config as Code (`railway.json`) is deprecated and stops being read on 2026-12-01, and new
 * services cannot opt into it, so this file is the supported description of the deployment.
 *
 * Secrets are never written here. DJANGO_SECRET_KEY uses preserve(), which keeps whatever is
 * already stored in Railway, so it must be set once out of band before the first apply.
 */
import {
  defineRailway,
  github,
  postgres,
  preserve,
  project,
  service,
  volume,
  type VariableValue,
} from "railway/iac";

/** A value Railway interpolates at runtime, for strings that mix a reference with literal text. */
const interpolated = (value: string): VariableValue => ({
  type: "raw",
  value: { value },
});

export default defineRailway(() => {
  const db = postgres("postgres");

  // Generated product derivatives live on MEDIA_ROOT. A container filesystem is replaced on every
  // redeploy, so without this volume the catalog would come back with its images missing.
  const media = volume("media", { sizeMB: 1024 });

  const app = service("app", {
    source: github("crazydiamond007/Elan", { branch: "master" }),
    // The repository Dockerfile is the build: pinned base digests, Tailwind compiled in a separate
    // stage, collectstatic at build time, and an unprivileged runtime user.
    build: { builder: "DOCKERFILE", dockerfilePath: "Dockerfile" },
    // /healthz/ touches no database and is exempt from the HTTPS redirect, so a failing health
    // check means the platform could not reach the application, not that PostgreSQL is down.
    healthcheck: "/healthz/",
    healthcheckTimeout: 300,
    volumeMounts: { "/app/media": media },
    env: {
      // The image binds Gunicorn to 0.0.0.0:8000, so Railway is told to use that port rather than
      // injecting one the application would ignore.
      PORT: "8000",
      WEB_CONCURRENCY: "2",
      DJANGO_SETTINGS_MODULE: "config.settings.production",

      // Health checks arrive with Host: healthcheck.railway.app, which production settings reject
      // unless it is listed; the public domain is interpolated by Railway at runtime.
      DJANGO_ALLOWED_HOSTS: interpolated(
        "${{RAILWAY_PUBLIC_DOMAIN}},healthcheck.railway.app",
      ),
      DJANGO_SITE_URL: interpolated("https://${{RAILWAY_PUBLIC_DOMAIN}}"),
      DJANGO_CSRF_TRUSTED_ORIGINS: interpolated(
        "https://${{RAILWAY_PUBLIC_DOMAIN}}",
      ),

      // TLS terminates at the platform. Without this every request redirects to itself.
      DJANGO_TRUST_PROXY_HTTPS: "true",
      // Single service, single domain: media is served from this origin through the one route that
      // matches generated product WebP names. See docs/deployment.md.
      DJANGO_SERVE_MEDIA: "true",
      DJANGO_HSTS_SECONDS: "0",
      DJANGO_SECRET_KEY: preserve(),

      // Reached over the private network, so the hostname is the database's private domain rather
      // than its public TCP proxy, and the port is the one PostgreSQL listens on internally.
      POSTGRES_HOST: db.env.RAILWAY_PRIVATE_DOMAIN,
      POSTGRES_PORT: "5432",
      POSTGRES_DB: db.env.PGDATABASE,
      POSTGRES_USER: db.env.PGUSER,
      POSTGRES_PASSWORD: db.env.PGPASSWORD,
      // Railway's PostgreSQL image presents a self-signed certificate whose subject alternative
      // name covers only localhost, so verify-full and verify-ca both fail against it. The
      // connection stays inside the project's private network and never crosses the internet.
      POSTGRES_SSLMODE: "require",
    },
  });

  return project("maison-elan", { resources: [app, db, media] });
});
