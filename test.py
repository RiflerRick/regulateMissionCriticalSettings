def get_position_to_comment(patch):
    """
        gets line number to comment

        :param payload: payload from the webhook
        :return: line number
        """
    # patch = file["patch"]
    patch = patch.split('@@')
    patch = patch[1].split(' ')
    preimage = patch[1]
    postimage = patch[2]
    preimage_start_line = preimage.split(',')[0]
    postimage_start_line = postimage.split(',')[0]
    position = 0
    return int(postimage_start_line)

patch = "@@ -1 +1,2 @@"
# patch = "@@ -0,0 +1 @@"
print get_position_to_comment(patch)
