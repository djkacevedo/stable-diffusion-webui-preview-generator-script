import modules.scripts as scripts
from modules import images
from modules.processing import process_images, Processed
from modules.processing import Processed
from modules.shared import opts, cmd_opts, state
from modules.shared import state
import os

import gradio as gr
from PIL import Image as im


import requests
import glob
from bs4 import BeautifulSoup
import pathlib
import html

def get_files_in_subdirectories(root_dir, is_recursive, accepted_extensions):
  root_dir = f"{root_dir.strip().rstrip('/')}/"
  paths = []
  filenames = []
  extensions = []
  for filepath in glob.iglob(root_dir + '**/*', recursive=is_recursive):
    if os.path.isdir(filepath):
      continue
    file_extension = pathlib.Path(filepath).suffix
    if file_extension in accepted_extensions:
      filename = pathlib.Path(filepath).name.replace(file_extension, '')
      paths.append(filepath)
      filenames.append(filename)
      extensions.append(file_extension)
  return paths, filenames, extensions

def get_subdirectories(root_dir):
  root_dir = f"{root_dir.strip().rstrip('/')}/"
  paths = []
  for filepath in glob.iglob(root_dir + '**/*', recursive=True):
    if os.path.isdir(filepath):
      paths.append(filepath.replace('\\','/'))
  return paths

def escape_parentheses(word):
  return word.replace('(','\(').replace(')','\)')

def get_parent_directory_name(path):
  return pathlib.Path(path).parent.name

def get_parent_directory_path(path):
  return pathlib.Path(path).parent

def read_file_tags(filename):
  tags = None
  with open(filename,'r') as file:
    tags = file.readlines()
    for i in range(len(tags)):
      tags[i] = tags[i].strip()
      tags[i] = tags[i].lower()
  return tags

def get_tags(soup, char):
  imgs = soup.find_all('img')
  imgs = [str(x) for x in imgs]

  found = None
  tags = None

  # get all image elements from soup
  for img in imgs:
    imgstr = str(img)
    if "title=" in imgstr and "rating" in imgstr:
      found = imgstr
      break

  if not found:
    return None
  else:
    tag_string = found.split('"')
    for j in range(len(tag_string)):
      if 'title=' in tag_string[j] and j+1 < len(tag_string):
        tag_string = tag_string[j+1]
        break
  tags = tag_string.strip() \
    .replace('  ', ' ') \
    .replace(' ', ',') \
    .replace('_', ' ') \
    .replace('&amp;#039;',"'") \
    .replace('&amp;lt;','\<') \
    .replace('&amp;gt;','\>') \
    .split(',')
  return tags

def get_name_tag(tags, name):
  if tags is None:
    return None
  name = name.replace('_', ' ')
  for tag in tags:
    if name in tag:
      return escape_parentheses(tag)
  return None

def format_tags(appearance_tags):
  formatted_tags = ""
  for tag in appearance_tags:
    formatted_tags += f", {escape_parentheses(tag)}"
  return formatted_tags

def filter_accepted_tags(accepted, actual):
  if actual is None:
    return None
  final_tags = []
  for tag in actual:
    if tag in accepted:
      final_tags.append(tag)
  return final_tags

def filter_bad_tags(bad, actual):
  if actual is None or bad is None:
    return None
  final_tags = []
  for tag in actual:
      if not tag in bad \
        and not "score" in tag \
        and not "rating" in tag:
        final_tags.append(tag)
  return final_tags

def get_search_name(name):
  mapping = [ ('_v2-768',''), \
              ('_v1',''), \
              ('_v2',''), \
              ('_v3',''), \
              ('_flat_chest',''), \
              ('_large_breasts',''), \
              ('_v2-768',''), \
              ('_bikini', ''), \
              ('_tennis', ''), \
              ('_classic', ''), \
              ('_rq', ''), \
              ('_chico_coco',''), \
              ('_cosplay',''), \
              ('casual',''), \
              ('nude',''), \
              ('pajamas',''), \
              ('_school_uniform',''), \
              ('FILL',''), \
              ('school',''), \
              ('_swimsuit',''), \
              ('_flat_chest',''), \
              ('_hime',''), \
              ('_detective',''), \
              ('_serafuku',''), \
              ('_bunnysuit',''), \
              ('_techwear',''), \
              ('_oba-chan',''), \
              ('_formal',''), \
              ('_commander',''), \
              ('_milf',''), \
              ('_gyaru',''), \
              ('_clown',''), \
              ('_armor',''), \
              ('_ye',''), \
              ('_nocloak',''), \
              ('_cloak',''), \
              ('_witch',''), \
              ('_lumituber',''), \
              ('_olivia',''), \
              ('_astral_dress',''), \
              ('_kimono',''), \
              ('_mother_nature',''), \
              ('_and_anya',''), \
              ('_prisma',''), \
              ('_hime',''), \
              ('_underling',''), \
              ('_girls',''), \
              ('_and_shimakaze',''), \
              ('krita_',''), \
              ('_and_mare',''), \
              ('ip_masquerena','i:p_masquerena'), \
              ('onimai','oyama_mahiro'), \
              ('artist_',''), \
              ('-thick_lines',''), \
              ('-v1',''), \
              ('-v2',''), \
              ('_large_breasts','')]

  search_name = name
  for k, v in mapping:
    search_name = search_name.replace(k, v)

  return search_name

def booru_escape(word):
  return word.replace('(','%28').replace(')','%29').replace("'",'%27').replace('!','%21').replace(':','%3a')

def main(p, overwrite_existing_images, use_gelbooru, model_path, show_results, filter_gelbooru):
  base_prompt = p.prompt.strip().rstrip(',')

  accepted_extensions = ['.safetensors','.pt','.ckpt','.bin']
  char_paths, chars, char_extentions = get_files_in_subdirectories(model_path, True, accepted_extensions);

  state.job_count = len(chars)

  # accepted_tags = read_file_tags("scripts/tags_good.txt")
  bad_tags = read_file_tags("scripts/tags_bad.txt")
  
  urls = [ [None] * 3 ] * len(chars)
  prompts = [None] * len(chars)
  
  imgs = []
  all_prompts = []
  infotexts = []

  for i in range(len(chars)):
    if state.interrupted:
      break

    search_name = get_search_name(chars[i])
    copyright_name = get_parent_directory_name(char_paths[i])
    parent_path = get_parent_directory_path(char_paths[i])

    network_call = None
    image_name = chars[i]
    if "models/Lora" in model_path:
      network_call = f"<lora:{chars[i]}:0.7>"
    elif "models/hypernetworks" in model_path:
      network_call = f"<hypernet:{chars[i]}:0.7>"
    elif "models/Stable-diffusion" in model_path:
      network_call = None
    elif "embeddings" in model_path:
      search_name = search_name.replace('_ti','')
      image_name += ".preview"
      network_call = f"({chars[i]}:1.1)"

    if filter_gelbooru:
      sort_string = f"sort%3arating%3adesc"
    else:
      sort_string = f"sort%3ascore%3adesc"

    if not overwrite_existing_images and os.path.isfile(f"{parent_path}/{image_name}.png"):
      print(f"Preview found, skipping {parent_path}/{chars[i]}{char_extentions[i]}")
      continue

    # Gelbooru
    urls[i][0] = f"https://gelbooru.com/index.php?page=post&s=list&tags={booru_escape(search_name)}%2a+solo+{booru_escape(copyright_name)}+{sort_string}"
    urls[i][1] = f"https://gelbooru.com/index.php?page=post&s=list&tags={booru_escape(search_name)}%2a+solo+{sort_string}"
    urls[i][2] = f"https://gelbooru.com/index.php?page=post&s=list&tags={booru_escape(search_name)}%2a+{sort_string}"

    if copyright_name == 'vtubers' and i == 0:
      continue

    print(f"Generating preview image for {copyright_name}/{chars[i]}{char_extentions[i]}")

    for j in range(3):
      if not filter_gelbooru and not j == 2:
        continue

      req = None
      soup = None
      char_tags = None
      appearance_tags = None

      if use_gelbooru:
        req = requests.get(urls[i][j], 'html.parser')
        soup = BeautifulSoup(req.content , 'html.parser')
        char_tags = get_tags(soup, chars[i])
        if filter_gelbooru:
          appearance_tags = filter_bad_tags(bad_tags, char_tags)
        else:
          appearance_tags = char_tags

      name_tag = get_name_tag(char_tags, search_name)
      
      escaped_search_name = escape_parentheses(search_name)
      escaped_copyright_name = escape_parentheses(copyright_name)

      if not use_gelbooru:
        prompts[i] = f"{base_prompt}, {network_call}, ({escaped_search_name}:1.1)"
        break
      elif name_tag is not None:
        formatted_tags = format_tags(char_tags)
        prompts[i] = f"{base_prompt}, {network_call}, ({name_tag}:1.1), {escaped_copyright_name}, ({formatted_tags}:0.9)"
        break
      elif appearance_tags is not None:
        formatted_tags = format_tags(char_tags)
        prompts[i] = f"{base_prompt}, {network_call}, ({escaped_search_name}:1.1), {escaped_copyright_name}, ({formatted_tags}:0.9)"
        break
      elif j == 2:
        prompts[i] = f"{base_prompt}, {network_call}, ({escaped_search_name}:1.1), {escaped_copyright_name}, "

    p.prompt = prompts[i]
    proc = process_images(p)

    if state.interrupted:
      break

    imgs += proc.images
    all_prompts += proc.all_prompts
    infotexts += proc.infotexts

    images.save_image(proc.images[0], parent_path, image_name, proc.seed, proc.prompt, "png", short_filename=True, forced_filename=image_name, info=proc.info, p=p)

  if show_results:
    return Processed(p, imgs, p.seed, "", all_prompts=all_prompts, infotexts=infotexts)
  else:
    return Processed(p, None, p.seed, "")


class Script(scripts.Script):
    is_txt2img = False

    # Function to set title
    def title(self):
        return "Preview Generator"

    def ui(self, is_img2img):

        with gr.Row():
          overwrite_existing_images = gr.Checkbox(label='Overwrite Existing Images')
          use_gelbooru = gr.Checkbox(label='Get tags from Gelbooru')
          filter_gelbooru = gr.Checkbox(label='Filter tags from Gelbooru')
          show_results = gr.Checkbox(label='Show Results')
        with gr.Row():
          # paths = ["embeddings","models/Lora","models/hypernetworks","models/Stable-diffusion"]
          paths = ["embeddings","models/Lora","models/hypernetworks"]
          for i in range(len(paths)):
            paths += get_subdirectories(paths[i])

          model_path = gr.Dropdown(label="path to models", choices = paths, value="models/Lora")

        return [overwrite_existing_images, use_gelbooru, model_path, show_results, filter_gelbooru]

    # Function to show the script
    def show(self, is_img2img):
        return True

    # Function to run the script
    def run(self, p, overwrite_existing_images, use_gelbooru, model_path, show_results, filter_gelbooru):
        # Make a process_images Object

        p.do_not_save_grid = True

        return main(p, overwrite_existing_images, use_gelbooru, model_path, show_results, filter_gelbooru)
