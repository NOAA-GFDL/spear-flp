using CSV
using DataFrames

include((@__DIR__)*"/../utilities/catalog_tools.jl")
using .CatalogTools

const catalog_csv = (@__DIR__) * "/../catalog_blue.csv"
const catalog_csv2 = (@__DIR__) * "/../catalog_blue2.csv"

function main(catalog)
    # catalog = DataFrame(CSV.File(catalog_csv; types=Dict("who_qc" => String)))
    to_move = search(catalog, Dict(:pass_qc => true, :path => "TFTEST"))

    for x in unique(to_move[!,:variable_id])
        for exp in unique(to_move[!,:experiment_id])
            search_dict = Dict(:variable_id => x, :experiment_id => exp)

            mv_var = search(to_move, search_dict)

            all_time_ranges = unique(search(catalog, search_dict)[!,:time_range])
            cand_time_ranges = unique(mv_var[!,:time_range])

            do_move = true
            for t in all_time_ranges
                if t ∉ cand_time_ranges
                    do_move = false
                    println("Nope!")
                    break
                end
            end

            if do_move
                for r in eachrow(mv_var)
                    p = r[:path]
                    out_path = replace(p, "TFTEST" => "SPEAR-MED-FLP")
                    # println("mv $p $out_path")
                    r[:path] = out_path
                end
                CSV.write(catalog_csv2, catalog)
            end
        end
    end
end

function fake_qc(d...)
    catalog = DataFrame(CSV.File(catalog_csv; types=Dict("who_qc" => String)))
    update!(search(catalog, d...), :pass_qc => true, :who_qc => "ariaradick")
    return catalog
end

main(fake_qc(:variable_id => "snow", :experiment_id => "SPEAR_c192_o1_Scen_SSP585_IC2011_K50"))