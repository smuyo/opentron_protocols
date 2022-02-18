od_csv = [[0.36,0.87,1,0-3,0.66,1,0.15,1,0.76,0.4,0.95,0.8],
    [0.36,0.87,1,0-3,0.66,1,0.15,1,0.76,0.4,0.95,0.8],
    [0.36,0.87,1,0-3,0.66,1,0.15,1,0.76,0.4,0.95,0.8],
    [0.36,0.87,1,0-3,0.66,1,0.15,1,0.76,0.4,0.95,0.8],
    [0.36,0.87,1,0-3,0.66,1,0.15,1,0.76,0.4,0.95,0.8],
    [0.36,0.87,1,0-3,0.66,1,0.15,1,0.76,0.4,0.95,0.8],
    [0.36,0.87,1,0-3,0.66,1,0.15,1,0.76,0.4,0.95,0.8],
    [0.36,0.87,1,0-3,0.66,1,0.15,1,0.76,0.4,0.95,0.8]]
target_od = 0.15
target_volume = 150

metadata = {
    'apiLevel' : '2.11',
    'protocolName' : 'OD Normalization',
    'author' : 'Sergi Muyo <sergimuyo@gmail.com',
    'description' : 'Produce a 96-well plate with a target OD'
}

def calculate_OD(initial_OD, final_OD, final_volume):
    if initial_OD <= final_OD:
        culture_OD = final_volume - 10
        media_OD = 10
    else:
        subpart = (final_OD * final_volume) // initial_OD
        media_OD = final_volume - subpart
        culture_OD = subpart
    return culture_OD, media_OD

def run(protocol):
    reservoir = protocol.load_labware('opentrons_6_tuberack_falcon_50ml_conical', 5)
    source = reservoir.wells()[0]

    tiprack_1 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    tiprack_2 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)

    wellplate_0 = protocol.load_labware('corning_96_wellplate_360ul_flat', 2)
    wellplate_1 = protocol.load_labware('corning_96_wellplate_360ul_flat', 3)

    l_pip = protocol.load_instrument('p300_single_gen2', 'left', [tiprack_1, tiprack_2])

    wp0_wells = []
    wp1_wells = []

    for row in wellplate_0.rows():
        wp0_wells += row

    for row in wellplate_1.rows():
        wp1_wells += row

    culture_vols = []
    media_vols = []

    for row in od_csv:
        for col in row:
            local_culture, local_media = calculate_OD(col, target_od, target_volume)
            culture_vols.append(local_culture)
            media_vols.append(local_media)

    mix_volume = target_volume // 3

    l_pip.transfer(media_vols, source, wp1_wells, new_tip='once')
    l_pip.transfer(culture_vols, wp0_wells, wp1_wells, new_tip='always', mix_after=(3,mix_volume))
