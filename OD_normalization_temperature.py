import copy

od_csv = [[1.0311,0.8877,0.8212,0.905,1.0634,0.981,1.1141,1.1325,1.0761,0.0878,0.0808,0.0822],
[1.0252,0.6736,0.5826,0.7862,0.1776,0.1881,0.8018,0.1637,0.1508,0.0853,0.0789,0.0818],
[1.0865,1.087,0.7625,0.9847,1.0645,1.0155,1.1232,0.9367,0.7712,0.0908,0.0841,0.0795],
[0.9976,0.8654,0.7189,0.845,0.1518,0.1862,0.8945,0.1578,0.1397,0.0863,0.0782,0.0792],
[0.2292,0.4016,0.4627,0.2966,0.5776,0.6074,0.3473,0.5193,0.4862,0.0794,0.081,0.0794],
[0.1993,0.1608,0.1807,0.2586,0.1811,0.1463,0.1789,0.1584,0.1478,0.0774,0.0774,0.0797],
[0.2056,0.3091,0.3435,0.2144,0.537,0.2256,0.3107,0.505,0.4718,0.0785,0.0817,0.0781],
[0.1922,0.1533,0.1637,0.1632,0.1554,0.1395,0.1704,0.1583,0.1605,0.0787,0.081,0.081]]
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

def custom_mix(times, pipette, location, volums):
    for i in range(times):
        pipette.aspirate(volums, location)
        pipette.dispense(volums, location, rate=3.33)

def run(protocol):
    temp_mod = protocol.load_module('temperature_module', 1)
    reservoir = protocol.load_labware('opentrons_6_tuberack_falcon_50ml_conical', 4)
    source = reservoir.wells()[0].top(z=-36)
    tr_tube = reservoir.wells()[5].top(z=-14)

    tiprack_1 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    tiprack_2 = protocol.load_labware('opentrons_96_tiprack_300ul', 5)
    tiprack_3 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)

    wellplate = temp_mod.load_labware('corning_96_wellplate_360ul_flat')
    l_pip = protocol.load_instrument('p300_single', 'left', [tiprack_1, tiprack_2, tiprack_3])

    temp_mod.set_temperature(4)

    source_dirs = []
    dest_dirs = []

    wp_rows = wellplate.rows()
    vols_transfer = []
    media_vols = []
    sources_list = [source]

    z_pos = -36
    used_vol = 0
    max_vol = 5000
    for row_num in range(len(od_csv)):
        if used_vol >= max_vol:
            z_pos -= 9
            max_vol += 5000
            source = reservoir.wells()[0].top(z=z_pos)
            sources_list.append(source)
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

    past_dest = ''
    for instru in range(len(vols_transfer)):
        curr_vol = vols_transfer[instru]
        curr_source = source_dirs[instru]
        curr_dest = dest_dirs[instru]
        if past_dest != curr_source:
            if l_pip.has_tip:
                l_pip.drop_tip()
        if curr_source in sources_list:
            if not l_pip.has_tip:
                l_pip.pick_up_tip()
            l_pip.transfer(curr_vol, curr_source, curr_dest, new_tip='never')
        else:
            if not l_pip.has_tip:
                l_pip.pick_up_tip()
            custom_mix(5, l_pip, curr_source, 100)
            l_pip.transfer(curr_vol, curr_source, curr_dest, new_tip='never')
            l_pip.drop_tip()
        past_dest = copy.deepcopy(curr_dest)
    if l_pip.has_tip:
        l_pip.drop_tip()
