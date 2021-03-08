# Hugo-2-Gopher-and-Gemini
A [Hugo](https://gohugo.io/) theme to convert a Hugo site to [Gopher](https://en.wikipedia.org/wiki/Gopher_%28protocol%29) and or [Gemini](https://en.wikipedia.org/wiki/Gemini_%28protocol%29) with the purpose of maintaining between one and three sites (a static web site, a Gopher hole, and a Gemini capsule). Each site may have different content. 

This theme is expected to be used as an additional theme. While, by default, your main theme will generate the site in the `public` folder, this additional theme will generate in `public-gg`. This requires two distinct executions of `hugo`, namely one for your regular theme, and one for this theme. There are no changes or side effects to your original Hugo site.

There are few use cases for this theme:
* A person with a current Hugo generated site that want to have presence in Gopher space or/and in Gemini space, while maintaining the original web site using Hugo. In this situation the person can use Hugo to maintain the web site, the Gopher hole and the Gemini capsule with some content in common between them, but other content specific to one or two of them.
* A person that wants to use Hugo to generate and maintain a Gemini capsule or Gopher hole.
* A person that wants to migrate a current Hugo web site to a Gemini capsule or a Gopher hole.

## Features
- Menu
- Social media links
- Do not generate HTML or RSS
- automatic conversion to Gopher
- Automatic conversion to Gemini

##  Installation & Update
In most cases, you will already have Hugo installed and have already a theme for your web site. This is the main use case and now you will install this theme as a new complementary theme (while maintaining your current theme). However, if you have not installed hugo follow the instructions at [quick start](https://gohugo.io/getting-started/quick-start/).

To add this theme to your current hugo site, just do:

```sh
git clone https://github.com/mkamarin/Hugo-2-Gopher-and-Gemini.git
```

For more information, see [Hugo docs](https://gohugo.io/themes/installing/). For upgrades, just do:

```sh
git submodule update --remote --merge
```

## Usage
1. You need to copy the `config-gg.toml` file to the main folder of your hugo site and edit it to adjust it to your situation. Note that now you have two distinct config files, namely one for your main theme (`config.toml`) and one for this theme (`config-gg.toml`).
2. If you plan to have content that is specific to Gopher and/or Gemini, you may want to use a naming convention for those posts. For example, you may name those posts `<name>-gg.md` and write them in a way that will look nice in Gopher and/or Gemini. In that case, you want to add the following line to your main `config.toml` file:

```toml
ignoreFiles =  ["-gg.md$"]
```

3. You need to create an empty folder called `layouts-gg`. This is done to avoid hugo from using the content in your main `layouts` folder.

```sh
mkdir layouts-gg
```

4. The `public-gg` folder will have two sub-folders, one for the Gopher hole named `public-gg/gopher` and one for the Gemini capsule named `public-gg/gemini`. There are two ways you can generate the `public-gg` folder:
   1- Execute `hugo2gg.py` located in this theme folder under `src'. In most cases, the default options will work fine. You can see all the options by executing `hugo2gg.py --help`. Based on the options, `hugo2gg.py` will execute hugo as the first step of the conversion. So, in most cases, you just want to execute it from the main folder of your hugo site as:

```sh
themes/Hugo-2-Gopher-and-Gemini/src/hugo2gg.py
```

    2- If you want to execute hugo manually before executing `hugo2gg.py`, you can do as follows:

```sh
hugo --config config-gg.toml --destination public-gg --layoutDir layouts-gg --disableKinds sitemap

themes/Hugo-2-Gopher-and-Gemini/src/hugo2gg.py --no-hugo
```


## License
GPLv3


 
