import re

def get_rows_columns_map(table_result, blocks_map):
    rows = {}
    for relationship in table_result['Relationships']:
        if relationship['Type'] == 'CHILD':
            for child_id in relationship['Ids']:
                cell = blocks_map[child_id]
                if cell['BlockType'] == 'CELL':
                    row_index = cell['RowIndex']
                    col_index = cell['ColumnIndex']
                    if row_index not in rows:
                        # create new row
                        rows[row_index] = {}

                    # get the text value
                    rows[row_index][col_index] = get_text(cell, blocks_map)
    return rows


def generate_table_csv(table_result, blocks_map, table_index):
    rows = get_rows_columns_map(table_result, blocks_map)

    table_id = 'Table_' + str(table_index)

    # get cells.
    csv = 'Table: {0}\n\n'.format(table_id)

    for row_index, cols in rows.items():

        for col_index, text in cols.items():
            csv += '{}'.format(text) + ","
        csv += '\n'

    csv += '\n\n\n'
    return csv


def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ' '
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] == 'SELECTED':
                            text += 'X '
    return text


def get_table_csv(doc):
    # Get the text blocks
    blocks = doc['Blocks']

    blocks_map = {}
    table_blocks = []
    for block in blocks:
        blocks_map[block['Id']] = block
        if block['BlockType'] == "TABLE":
            table_blocks.append(block)

    if len(table_blocks) <= 0:
        return "<b> NO Table FOUND </b>"

    csv = ''
    for index, table in enumerate(table_blocks):
        csv += generate_table_csv(table, blocks_map, index + 1)
        csv += '\n\n'
    return csv


def get_pageline_map(doc):
    blocks = doc['Blocks']
    page_child_map = {}
    page_lines = {}

    for block in blocks:
        if block['BlockType'] == "PAGE":
            if 'CHILD' in block['Relationships'][0]['Type']:
                page_child_map[block['Page']] = block['Relationships'][0]['Ids']
        if block['BlockType'] == "LINE":
            if block['Id'] in page_child_map[block['Page']]:
                if block['Page'] in page_lines:
                    page_lines[block['Page']].append(block['Text'])
                else:
                    page_lines[block['Page']] = [block['Text']]
    return page_lines


def get_restructpagelines(doc):
    pages = {}
    for page in doc.items():
        prev_y = None
        lines = []
        ln = ''
        for line in page[1]:
            text = line[0]['Text']
            y = line[0]['BoundingBox']['Top']
            if len(ln) == 0:
                ln = text
            elif prev_y - 0.005 <= y <= prev_y + 0.005:
                ln += " \t" + text
            elif len(ln) != 0:
                lines.append(ln)
                ln = text
            else:
                lines.append(text)
            prev_y = y
        lines.append(ln)
        pages[page[0]] = lines
    return pages


def get_pagelineinfo_map(doc):
    blocks = doc['Blocks']
    page_child_map = {}
    pagelineinfo = {}

    for block in blocks:
        if block['BlockType'] == "PAGE":
            if 'CHILD' in block['Relationships'][0]['Type']:
                page_child_map[block['Page']] = block['Relationships'][0]['Ids']
        if block['BlockType'] == "LINE":
            if block['Id'] in page_child_map[block['Page']]:
                if block['Page'] in pagelineinfo:
                    pagelineinfo[block['Page']].append([{'LineNum':len(pagelineinfo[block['Page']])+1,
                                                        'Text': block['Text'], 'Confidence': block['Confidence'],
                                                       'BoundingBox': block['Geometry']['BoundingBox']}])
                else:
                    pagelineinfo[block['Page']] = [[{'LineNum': 1, 'Text': block['Text'], 'Confidence': block['Confidence'],
                                                        'BoundingBox': block['Geometry']['BoundingBox']}]]
    return pagelineinfo


def get_pageinfo(doc):
    blocks = doc['Blocks']
    pages = {}
    for block in blocks:
        if block['BlockType'] == "PAGE":
            pages[block['Page']] = block
    return pages


def get_kv_map(doc):
    blocks = doc['Blocks']
    # get key and value maps
    key_map = {}
    value_map = {}
    block_map = {}
    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block
    return key_map, value_map, block_map


def get_kv_relationship(key_map, value_map, block_map):
    kvs = {}
    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map)
        key = get_text(key_block, block_map)
        val = get_text(value_block, block_map)
        kvs[key] = val
    return kvs


def find_value_block(key_block, value_map):
    for relationship in key_block['Relationships']:
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                value_block = value_map[value_id]
    return value_block


def print_kvs(kvs):
    for key, value in kvs.items():
        print(key, ":", value)


def get_kv_pairs(result, display=False):
    key_map, value_map, block_map = get_kv_map(result)

    # Get Key Value relationship
    kvs = get_kv_relationship(key_map, value_map, block_map)
    if display:
        show_kv_pairs(kvs)
    return kvs


def show_kv_pairs(kvs):
    print("\n\n== FOUND KEY : VALUE pairs ===\n")
    print_kvs(kvs)


def search_value(kvs, search_key):
    for key, value in kvs.items():
        if re.search(search_key, key, re.IGNORECASE):
            return value