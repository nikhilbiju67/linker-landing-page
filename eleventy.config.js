// The Linkker blog: blog-src/ -> blog/ (committed, served as static files by Vercel).
export default function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy({ "blog-src/assets": "assets" });

  eleventyConfig.addFilter("isoDate", (d) => new Date(d).toISOString());
  eleventyConfig.addFilter("readableDate", (d) =>
    new Date(d).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })
  );
  eleventyConfig.addFilter("domain", (u) => {
    try { return new URL(u).hostname.replace(/^www\./, ""); } catch { return u; }
  });
  eleventyConfig.addFilter("md", (s) => (s ? md.render(String(s)) : ""));
  eleventyConfig.addFilter("mdInline", (s) => (s ? md.renderInline(String(s)) : ""));

  // Drafts stay out of the build until publish.sh moves them into posts/.
  eleventyConfig.addCollection("posts", (api) =>
    api.getFilteredByGlob("blog-src/posts/*.md").sort((a, b) => b.date - a.date)
  );

  // Every post links to three others, same pillar first, so a new post on a young
  // domain is reachable from the whole archive and not only from /blog/.
  eleventyConfig.addFilter("related", (posts, url, limit = 3) => {
    const self = posts.find((p) => p.url === url);
    const pillar = self && self.data.pillar;
    const same = (p) => (pillar && p.data.pillar === pillar ? 0 : 1);
    return posts
      .filter((p) => p.url !== url)
      .sort((a, b) => same(a) - same(b) || b.date - a.date)
      .slice(0, limit);
  });

  let md;
  eleventyConfig.amendLibrary("md", (lib) => { md = lib; });

  return {
    dir: { input: "blog-src", output: "blog", includes: "_includes", data: "_data" },
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk",
  };
}
