# stable-diffusion-webui-preview-generator-script
script for Automatic1111's webui to one click generate previews for all of your models

Generates preview images for embeddings, loras, and hypernetworks, selectable by drop down; recursively generates everything within a selcted directory.

This will work out of the box, without any tinkering, especially for embeddings and hypernetworks. For you to get real value out of this for loras, the lora files need to be named after their trigger words. If you want gelbooru to help, then naming the file the same as the booru tag for their name (character or author) will help for when the script tries to get tags for them.

Installation: Just copy the script to your webui scripts folder.

Usage:
All of the generation data will be used as expected, and if you have "Get tags from Gelbooru" checked, then it'll attempt to get tags and add them to the end of your prompt.

Overwrite Existing Images: if checked, it'll overwrite existing preview images. If unchecked, it won't generate anything if an image already exists.
Get tags from Gelbooru: if checked, it will attempt to get appearance tags from gelbooru.
Filter tags from Gelbooru: if checked, it'll attempt to filter out nsfw and meta tags.
Show Results: if checked, will show results.
path to models: drop down for all of your model directories that this will work for.

WARNING: if you already have previews you like, then do not select the folder's they're in, or do not check the overwrite box.

Also of note: if you check filter tags, then it sorts by rating instead of score, so your a lot less likely to get tags based on a lewd image.
