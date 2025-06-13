using DataFrames
using CSV

const catalog_csv = "catalog_blue.csv"
const allowed_keys = ["variable_id", "experiment_id", "time_range", "member_id"]

function string_to_vector(x)
    strip.(split(strip(x, ['[',']',' ']),','))
end

function body_to_dict(input_string, allowed_vars)
    var_dict = Dict{Symbol,Vector{String}}()
    y = strip.(split(input_string,'\n'))
    y = y[[3,7,11,15]]

    if y[1] in allowed_vars
        var_dict[:variable_id] = [y[1]]
    else
        error("Variable name does not exist in catalog.")
    end

    if y[2] == "Historical"
        var_dict[:experiment_id] = ["SPEAR_c192_o1_Hist_AllForc_IC1921_K50"]
    elseif y[2] == "SSP585"
        var_dict[:experiment_id] = ["SPEAR_c192_o1_Scen_SSP585_IC2011_K50"]
    end

    if (y[3] ≠ "_No response_")
        var_dict[:time_range] = string_to_vector(y[3])
    end

    if y[4] == "Yes"
        pass_qc = true
    elseif y[4] == "No"
        pass_qc = false
    end

    return var_dict, pass_qc
end

function find_rows(df, columns)
    truths = ones(Bool, size(df)[1])
    for (k,v) in columns
        if k == "experiment_id"
            subtruths = zeros(Bool, size(df)[1])
            for x in v
                subtruths = (subtruths .| occursin.(x,df[!,k]))
            end
            truths = (truths .& subtruths)
        else
            subtruths = zeros(Bool, size(df)[1])
            for x in v
                subtruths = (subtruths .| (df[!,k] .== x))
            end
            truths = (truths .& subtruths)
        end
    end
    return truths
end

function update_qc!(df, columns, qc_status, who_qc)
    truths = find_rows(df, columns)
    df[truths,:pass_qc] .= qc_status
    df[truths,:who_qc] .= who_qc
    return df[truths,:]
end

function main(x)
    df = DataFrame(CSV.File(catalog_csv; types=Dict("who_qc" => String)))
    allowed_vars = unique(df[!,:variable_id])

    username = x[1]
    param_dict, pass_qc = body_to_dict(x[2], allowed_vars)

    update_qc!(df, param_dict, pass_qc, username)
    CSV.write(catalog_csv, df)
end

main(ARGS)