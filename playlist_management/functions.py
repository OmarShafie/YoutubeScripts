""" Omar Shafie (OSMIUM), June 2018.

 This is a simple project that uses Youtube API v3.

 It manages my personal watch list on Youtube.
 It sorts videos by channels in round robin order.
"""
import time
# Build a resource based on a list of properties given as key-value pairs.
# Leave properties with empty values out of the inserted resource.
def build_resource(properties):
    """ Taken from API Doc """
    resource = {}
    for prop in properties:
        # Given a key like "snippet.title", split into "snippet" and "title", where
        # "snippet" will be an object and "title" will be a property in that object.
        prop_array = prop.split('.')
        ref = resource
        for parr in range(0, len(prop_array)):
            is_array = False
            key = prop_array[parr]

            # For properties that have array values, convert a name like
            # "snippet.tags[]" to snippet.tags, and set a flag to handle
            # the value as an array.
            if key[-2:] == '[]':
                key = key[0:len(key)-2:]
                is_array = True

            if parr == (len(prop_array) - 1):
                # Leave properties without values out of inserted resource.
                if properties[prop]:
                    if is_array:
                        ref[key] = properties[prop].split(',')
                    else:
                        ref[key] = properties[prop]
            elif key not in ref:
                # For example, the property is "snippet.title", but the resource does
                # not yet have a "snippet" object. Create the snippet object here.
                # Setting "ref = ref[key]" means that in the next time through the
                # "for pa in range ..." loop, we will be setting a property in the
                # resource's "snippet" object.
                ref[key] = {}
                ref = ref[key]
            else:
                # For example, the property is "snippet.description", and the resource
                # already has a "snippet" object.
                ref = ref[key]
    return resource

def playlist_item_update_position(client, properties, **kwargs):
    """ Updates a single position of an item. """
    resource = build_resource(properties)

    client.playlistItems().update(
        body=resource,
        **kwargs
    ).execute()

def video_by_id(client, **kwargs):
    """ Extracts the channelId for the passed video """
    response = client.videos().list(**kwargs).execute()

    if response:
        channel_id = response["items"][0]["snippet"]["channelId"]

    return channel_id

def list_playlist_items(client, playlist_id):
    """ Fetches the videos in my watch list.

    It requests for the playlist items in pages of size 50 items.
    While a new page token is given it retrieves it.
    Combines all items in a list.

    Returns:
        A list of all items (dictionaries) in my watch list.
    """
    start = time.time()
    # request for playlist items at playlist_id, this is for the 1st page only
    req = client.playlistItems().list(
        part='snippet,contentDetails',
        maxResults=50,
        playlistId=playlist_id)

    # list of video items (dictionary)
    items = []

    # retrieve all pages
    while req:
        res = req.execute()
        items += res["items"]
        req = client.playlistItems().list_next(req, res)

    end = time.time()
    print "\n 1/3 Finished in " +str(end- start)+" seconds. \n"

    return items

def get_video_details(client, item):
    """ Fetches the video details and cleans up unnecessary info.

    Since channelId is not available in contentDetails, we have
        to make a GET request for it.

    Args:
        client: Duh!
        item: An item that has contentDetails and id of any video.

    Returns:
        A dictionary of the needed details of the item.:
            - chan_id: channel id of that uploaded the video.
            - id: of the video in the playlist?
            - videoId: another id that is needed.
            - time_stamp: of when the video was published.
    """
    video_id = item["contentDetails"]["videoId"]
    time_stamp = item["contentDetails"]["videoPublishedAt"]
    vid = item["id"]

    chan_id = video_by_id(client, part='snippet', id=video_id)

    ### output.put({"chan_id": chan_id, "id": id, "videoId": videoId})
    result = {"chan_id": chan_id, "id": vid,
              "videoId": video_id, "time_stamp": time_stamp}
    return result

def sort_by_channels(client, items):
    """ Organize the list of all videos into a dictionary of channels

    Creates a dictionary of channels in items and their corresponding videos
    sorted by time published.

    """
    start = time.time()
    #output = mp.Queue()
    #pool = mp.Pool(processes=4)

    #results = [pool.apply(get_video_details, args=(client,content, v, output))
        #for v in range(len(content))]

    # TODO : PARALLELIZE
    # TODO : CACHE-ABLE
    results = [get_video_details(client, items[i]) for i in range(len(items))]

    # dict of channel_id as key, list of video from that channel as values
    dic = {}
    for vid in results:
        chan_id = vid["chan_id"]
        if chan_id in dic:
            dic[chan_id].append(vid)
        else:
            dic[chan_id] = [vid]

    for chnl in dic:
        dic[chnl].sort(key=lambda x: x['time_stamp'])

    end = time.time()
    print "\n 2/3 Finished in " +str(end- start)+" seconds. \n"

    return dic

def ordered_list(dic_channels):
    """ Round-Robin oreder of the items in dictionary """
    ordered = []
    old_len = -1
    index = 0
    while len(ordered) > old_len:
        old_len = len(ordered)
        for channel in dic_channels:
            if len(dic_channels[channel]) > index:
                ordered += [dic_channels[channel][index]]
        index += 1

    return ordered

def update_all(client, videos, playlist_id):
    """ Updates the position in the watchlist as the order in videos"""
    start = time.time()
    pos = 0

    # TODO : PARALLELIZE
    for item in videos:
        properties = {
            'id': item["id"],
            'snippet.playlistId': playlist_id,
            'snippet.resourceId.kind': 'youtube#video',
            'snippet.resourceId.videoId': item["videoId"],
            'snippet.position': pos
        }

        playlist_item_update_position(client, properties, part='snippet')
        pos += 1

    end = time.time()
    print "\n 3/3 Finished in " +str(end- start)+" seconds. \n"
