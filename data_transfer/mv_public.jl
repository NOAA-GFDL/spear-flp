using CSV
using DataFrames

include((@__DIR__)*"/../utilities/catalog_tools.jl")
using .CatalogTools

const catalog_csv = (@__DIR__) * "/../catalog_blue.csv"
const catalog_csv2 = (@__DIR__) * "/../catalog_blue2.csv"

function git_pull()
    run(Cmd(`git checkout dev`))
    run(Cmd(`git pull`))
end

function git_push(msg)
    run(Cmd(`git add .`))
    run(Cmd(`git commit -m $msg`))
    run(Cmd(`git push`))
end

function fake_qc(d...)
    catalog = DataFrame(CSV.File(catalog_csv; types=Dict("who_qc" => String)))
    update!(search(catalog, d...), :pass_qc => true, :who_qc => "ariaradick")
    return catalog
end

function short_exp(experiment_id)
    if experiment_id == "SPEAR_c192_o1_Scen_SSP585_IC2011_K50"
        return "SSP585"
    elseif experiment_id == "SPEAR_c192_o1_Hist_AllForc_IC1921_K50"
        return "Historical"
    end
end

function main()
    git_pull()
    # catalog = DataFrame(CSV.File(catalog_csv; types=Dict("who_qc" => String)))
    catalog = fake_qc(:variable_id => "snow", :experiment_id => "SPEAR_c192_o1_Scen_SSP585_IC2011_K50")
    to_move = search(catalog, Dict(:pass_qc => true, :path => "TFTEST"))

    var_exp = []

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
                push!(var_exp, (String(x), short_exp(exp)))
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

    var_string = join("(" .* join.(var_exp,", ") .* ")", ", ")
    git_push("Moved $var_string")
end

main()
