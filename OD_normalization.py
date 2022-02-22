od_csv = [[0.36,0.87,1,0.3,0.66,1,0.15,1,0.76,0.4,0.95,0.8],
    [0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.55,0.6,0.65,0.7],
    [0.75,0.8,0.85,0.9,0.95,1,0.15,1,0.76,0.4,0.95,0.8],
    [0.36,0.87,1,0.3,0.66,1,0.15,1,0.76,0.4,0.95,0.8],
    [0.36,0.87,1,0.3,0.66,1,0.15,1,0.76,0.4,0.95,0.8],
    [0.36,0.87,1,0.3,0.66,1,0.15,1,0.76,0.4,0.95,0.8],
    [0.36,0.87,1,0.3,0.66,1,0.15,1,0.76,0.4,0.95,0.8],
    [0.36,0.87,1,0.3,0.66,1,0.15,1,0.76,0.4,0.95,0.8]]
target_od = 0.15
top_od = 0.2
initial_volume = 150
target_volume = 150
vol_well = 300

metadata = {
    'apiLevel' : '2.11',
    'protocolName' : 'OD Normalization',
    'author' : 'Sergi Muyo <sergimuyo@gmail.com',
    'description' : 'Produce a 96-well plate with a target OD'
}

def calculate_OD(initial_OD, final_OD, final_volume, start_volume, max_intermediate, max_od):
    out_vols = []

    subpart = round((final_OD * final_volume) / initial_OD)
    aspir_vol = start_volume - subpart

    if aspir_vol == 0:
        return out_vols

    if aspir_vol <= start_volume - 50:
        out_vols.append(aspir_vol)
        out_vols.append(aspir_vol)

    else:
        first_aspir = start_volume - 50
        out_vols.append(first_aspir)
        volume_need = round((50 * initial_OD) / final_OD)

        if volume_need <= max_intermediate:
            media_vol = volume_need - 50
            out_vols.append(media_vol)
            well_out = volume_need - final_volume
            out_vols.append(well_out)
        else:
            media_vol = max_intermediate - 50
            out_vols.append(media_vol)
            new_OD = (50 * initial_OD) / max_intermediate
            if new_OD < max_od:
                out_vols.append(max_intermediate - final_volume)
            else:
                second_vols = calculate_OD(new_OD, final_OD, final_volume, max_intermediate, max_intermediate, max_od)
                for volume in second_vols:
                    out_vols.append(volume)
    return out_vols

def run(protocol):
    reservoir = protocol.load_labware('opentrons_6_tuberack_falcon_50ml_conical', 6)
    source = reservoir.wells()[0].top(z=-36)
    tr_tube = reservoir.wells()[5].top(z=-14)

    tiprack_1 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    tiprack_2 = protocol.load_labware('opentrons_96_tiprack_300ul', 5)
    tiprack_3 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)

    wellplate = protocol.load_labware('corning_96_wellplate_360ul_flat', 2)

    l_pip = protocol.load_instrument('p300_single', 'left', [tiprack_1, tiprack_2, tiprack_3])

    source_dirs = []
    dest_dirs = []

    wp_rows = wellplate.rows()
    vols_transfer = []
    media_vols = []

    z_pos = -36
    used_vol = 0
    max_vol = 5000
    for row_num in range(len(od_csv)):
        if used_vol >= max_vol:
            z_pos -= 9
            max_vol += 5000
            source = reservoir.wells()[0].top(z=z_pos)
        for col_num in range(len(od_csv[row_num])):
            if od_csv[row_num][col_num] <= target_od:
                continue
            volumes = calculate_OD(od_csv[row_num][col_num], target_od, target_volume, initial_volume, vol_well, top_od)
            for vol_num in range(len(volumes)):
                used_vol += volumes[vol_num]
                vols_transfer.append(volumes[vol_num])
                if vol_num%2 == 0:
                    source_dirs.append(wp_rows[row_num][col_num])
                    dest_dirs.append(tr_tube)
                else:
                    source_dirs.append(source)
                    dest_dirs.append(wp_rows[row_num][col_num])

    mix_volume = round(target_volume / 3)

    l_pip.transfer(vols_transfer, source_dirs, dest_dirs, new_tip='always', mix_before=(3,mix_volume))
