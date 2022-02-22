od_csv = [[1.357,1.29,1.223,1.135,1.052,0.956,0.863,0.715,0.538,0.333,0.086,0.087],
[1.286,1.23,1.18,1.085,1.025,0.957,0.858,0.698,0.547,0.323,0.088,0.088],
[0.089,0.088,0.089,0.087,0.089,0.09,0.09,0.089,0.088,0.087,0.087,0.087],
[0.09,0.087,0.088,0.089,0.089,0.091,0.091,0.091,0.089,0.088,0.087,0.088],
[0.088,0.089,0.087,0.089,0.089,0.089,0.09,0.089,0.088,0.088,0.087,0.089],
[0.088,0.089,0.091,0.092,0.088,0.09,0.089,0.088,0.089,0.087,0.09,0.088],
[0.089,0.082,0.089,0.088,0.088,0.089,0.089,0.089,0.089,0.088,0.09,0.09],
[0.088,0.083,0.089,0.089,0.087,0.088,0.09,0.087,0.087,0.089,0.09,0.09]]
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
    if aspir_vol <= 0:
        return out_vols
    if aspir_vol <= start_volume - 50:
        out_vols.append(aspir_vol)
        if start_volume > final_volume:
            aspir_vol2 = final_volume - (start_volume - aspir_vol)
        elif start_volume == final_volume:
            aspir_vol2 = aspir_vol
        else:
            aspir_vol2 = final_volume - (start_volume - aspir_vol)
        out_vols.append(aspir_vol2)
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
