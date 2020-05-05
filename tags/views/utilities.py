
# Should be moved client side
def toggle_tag(selected_tags, tag):
    tag_list = [tag for tag in selected_tags]

    if tag in selected_tags:
        tag_list.remove(tag)
    else:
        tag_list.append(tag)

    tag_list.sort()
    return ",".join(tag_list)

# Parse the tags added in an entry
def parse_tags(tags_string):

    tags_list = []

    tags_string = tags_string.strip() # Remove useless spaces
    tags_string = tags_string.split(",") # Split by commas

    tags_list = filter(lambda s: len(s) > 0, tags_string)

    return tags_list

