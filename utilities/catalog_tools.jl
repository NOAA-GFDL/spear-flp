module CatalogTools

export search, update!

using CSV
using DataFrames

function _search_i(df, k, v)
    if k == :path
        return occursin.(v, df[!,k])
    else
        return (df[!,k] .== v)
    end
end

function _search_idx(df, args...)
    truths = ones(Bool, size(df)[1])
    for (k,v) in args
        if typeof(v) <: AbstractString
            truths .&= _search_i(df,k,v)
        else
            subtruths = zeros(Bool, size(df)[1])
            for x in v
                subtruths .|= _search_i(df,k,x)
            end
            truths .&= subtruths
        end
    end
    return truths
end

function search(df, args...)
    return @view df[_search_idx(df, args...),:]
end

function search(df, args::Tuple...)
    truths = zeros(Bool, size(df)[1])
    for a in args
        truths .|= _search_idx(df, a...)
    end
    return @view df[truths,:]
end

function search(df, args::Dict...)
    truths = zeros(Bool, size(df)[1])
    for a in args
        truths .|= _search_idx(df, a...)
    end
    return @view df[truths,:]
end

function update!(df, args...)
    for (k,v) in args
        df[!,k] .= v
    end
end

end