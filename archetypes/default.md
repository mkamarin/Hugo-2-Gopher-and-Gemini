---
# Typical hugo front matter
title: "{{ replace .Name "-" " " | title }}"
date: {{ .Date }}
description: ""
tags: [""]
categories: [""]
draft: true

## Front matter to control Hugo-2-Gopher-and-Gemini:

# Outputs is used to limit the generation of this page
# for example, if you want a page to be generated for gopher only
# you will use: 'outputs: ["gopher"]'
# Uncomment the next line to use it
#outputs: ["html", "rss", "gemini", "gopher"]

# Keep raw will just keep the raw page as it was writen. In other words,
# no convertion process will be done in the page. Useful if the page was
# writen specifically for Gopher or for Gemini and you use the corresponding 
# outputs (above)
ggKeepRaw: false

# Remove extras will not generate extras for this page. Extras are controlled
# in the config.gg.toml under [params.gopher] and [params.gemini]. Their names
# start with 'include'. They are Menu, Categories, Social, Return home, and
# Author. This is useful if you wants a specific page to be different.
ggRemoveExtras: false

# Copy page will force hugo2gg.py to copy this page from the 'last' directory.
# This uses the 'hugo2gg.py --last' option (default to public-gg-sav).
# Useful when you manually modify a generated page and want to keep your
# changes. In that case you will copy your modified site to a directory, and
# execute hugo2gg.py with the correct --last option.
ggCopyPage: false

# Ignore links will ignore the links in the page. Links will not be generated
# for that page. Useful for pages where the links are not that important, and 
# you don't want to include them in Gopher or Gemini.
ggIgnoreLinks: false

---

