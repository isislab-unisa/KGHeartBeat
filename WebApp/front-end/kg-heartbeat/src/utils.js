import parseISO from 'date-fns/parseISO';

function trasform_to_series(quality_data,selectedKGs,quality_dimension,quality_metric,custom_series_name){
    let series = []
    for(let i = 0; i< selectedKGs.length; i++){
        let serie = {
            id : selectedKGs[i].id,
            name: custom_series_name,
            data : [],
            linkedTo: quality_metric,
            stack: ''
        }
        series.push(serie)
    }
    for(let i = 0; i < quality_data.length; i++){
        for(let j = 0; j<selectedKGs.length; j++){
            if (selectedKGs[j].id === quality_data[i].kg_id){
                const tab_date = quality_data[i].analysis_date.split('-');
                const date_utc = Date.UTC(parseInt(tab_date[0]),parseInt(tab_date[1])-1,parseInt(tab_date[2]));
                if(quality_data[i].Quality_category_array[quality_dimension].hasOwnProperty(quality_metric)){
                    series[j].data.push([date_utc,parseFloat(quality_data[i].Quality_category_array[quality_dimension][quality_metric])])
                    if(series[j].stack === '')
                        series[j].stack = quality_data[i].kg_name;
                    if(series[j].name === '' || series[j].name === undefined)
                        series[j].name = quality_data[i].kg_name;
                }
            }
        }
    }
    return series
}

function trasform_to_series_sparql_av(quality_data,selectedKGs,quality_dimension,quality_metric,custom_series_name){
    let series = []
    for(let i = 0; i< selectedKGs.length; i++){
        let serie = {
            id : selectedKGs[i].id,
            name: custom_series_name,
            data : [],
            lineWidth: 3,
            zones:[{
                value: 0.95,
                color: '#fd5e53'
            },
            { color: '#90ed7d'
            }
            ], 
        }
        series.push(serie)
    }
    for(let i = 0; i < quality_data.length; i++){
        for(let j = 0; j<selectedKGs.length; j++){
            if (series[j].id === quality_data[i].kg_id){
                const tab_date = quality_data[i].analysis_date.split('-');
                const date_utc = Date.UTC(parseInt(tab_date[0]),parseInt(tab_date[1])-1,parseInt(tab_date[2]));
                let availability = quality_data[i].Quality_category_array[quality_dimension][quality_metric]
                if(availability === 'Available' || availability === '1')
                    series[j].data.push([date_utc,1])
                else if(availability === 'offline' || availability === '0')
                    series[j].data.push([date_utc,0])
                else if(availability === '-' || availability === '-1')
                    series[j].data.push([date_utc,-1])
                else
                    series[j].data.push([date_utc,-1])
                if(series[j].stack === '')
                    series[j].stack = quality_data[i].kg_name;
                if(series[j].name === '' || series[j].name === undefined)
                    series[j].name = quality_data[i].kg_name;
            }
        }
    }
    series[0].data.sort()
    return series
}


/*This function is useful when we have analysis data over different time from the db, and we want to compact in an array with a number of values equal to the number of kg  */
function compact_temporal_data(quality_data,selectedKGs,quality_dimension,quality_metric){
    let series = []
    for(let i = 0; i< selectedKGs.length; i++){
        let serie = {
            id : selectedKGs[i].id,
            name: '',
            data : []
        }
        series.push(serie)
    }
    for(let i = 0; i < quality_data.length; i++){
        for(let j = 0; j<selectedKGs.length; j++){
            if (series[j].id === quality_data[i].kg_id){
                const tab_date = quality_data[i].analysis_date.split('-');
                const date_utc = Date.UTC(parseInt(tab_date[0]),parseInt(tab_date[1])-1,parseInt(tab_date[2]));
                if(quality_data[i].Quality_category_array[quality_dimension].hasOwnProperty(quality_metric)){
                    if(!isNaN(parseFloat(quality_data[i].Quality_category_array[quality_dimension][quality_metric]))){
                        series[j].data.push([date_utc,parseFloat(quality_data[i].Quality_category_array[quality_dimension][quality_metric])])
                    } else {
                        series[j].data.push([date_utc,'-'])
                    }
                    if(series[j].name === '')
                        series[j].name = quality_data[i].kg_name;
                }
            }
        }
    }
    return series
}

/*This function is useful when we have analysis data over different time from the db, and we want to compact in an array with a number of values equal to the number of kg  */
function compact_string_temporal_data(quality_data,selectedKGs,quality_dimension,quality_metric){
    let series = []
    for(let i = 0; i< selectedKGs.length; i++){
        let serie = {
            id : selectedKGs[i].id,
            name: '',
            data : []
        }
        series.push(serie)
    }
    for(let i = 0; i < quality_data.length; i++){
        for(let j = 0; j<selectedKGs.length; j++){
            if (series[j].id === quality_data[i].kg_id){
                const tab_date = quality_data[i].analysis_date.split('-');
                const date_utc = Date.UTC(parseInt(tab_date[0]),parseInt(tab_date[1])-1,parseInt(tab_date[2]));
                if(quality_data[i].Quality_category_array[quality_dimension].hasOwnProperty(quality_metric)){
                    series[j].data.push([date_utc,quality_data[i].Quality_category_array[quality_dimension][quality_metric]])
                    if(series[j].name === '')
                        series[j].name = quality_data[i].kg_name;
                }
            }
        }
    }
    return series
}

function trasform_latency_to_series(quality_data,selectedKGs,quality_dimension){
    let series = []
    for(let i = 0; i< selectedKGs.length; i++){
        let serie = {
            id : selectedKGs[i].id,
            name: '',
            data : []
        }
        series.push(serie)
    }
    for(let i = 0; i < quality_data.length; i++){
        for(let j = 0; j<selectedKGs.length; j++){
            if (series[j].id === quality_data[i].kg_id){
                const tab_date = quality_data[i].analysis_date.split('-');
                const date_utc = Date.UTC(parseInt(tab_date[0]),parseInt(tab_date[1])-1,parseInt(tab_date[2]));
                const  dimension_obj =  quality_data[i].Quality_category_array[quality_dimension]
                series[j].data.push([date_utc,parseFloat(dimension_obj.minLatency),parseFloat(dimension_obj.percentile25L),parseFloat(dimension_obj.medianL),parseFloat(dimension_obj.percentile75L),parseFloat(dimension_obj.maxLantency)])
                if(series[j].name === '')
                    series[j].name = quality_data[i].kg_name;
            }
        }
    }
    return series
}

function trasform_throughput_to_series(quality_data,selectedKGs,quality_dimension){
    let series = []
    for(let i = 0; i< selectedKGs.length; i++){
        let serie = {
            id : selectedKGs[i].id,
            name: '',
            data : []
        }
        series.push(serie)
    }
    for(let i = 0; i < quality_data.length; i++){
        for(let j = 0; j<selectedKGs.length; j++){
            if (series[j].id === quality_data[i].kg_id){
                const tab_date = quality_data[i].analysis_date.split('-');
                const date_utc = Date.UTC(parseInt(tab_date[0]),parseInt(tab_date[1])-1,parseInt(tab_date[2]));
                const  dimension_obj =  quality_data[i].Quality_category_array[quality_dimension]
                series[j].data.push([date_utc,parseFloat(dimension_obj.minThroughput),parseFloat(dimension_obj.percentile25T),parseFloat(dimension_obj.medianT),parseFloat(dimension_obj.percentile75T),parseFloat(dimension_obj.maxThrougput)])
                if(series[j].name === '')
                    series[j].name = quality_data[i].kg_name;
            }
        }
    }
    return series
}

function get_analysis_date(quality_data){
    let parsed_date = []
    for(let i = 0; i<quality_data.length; i++){
        parsed_date.push(parseISO(quality_data[i].analysis_date))
    }   
    return parsed_date
}

function find_target_analysis(quality_data,analysis_date,selectedKGs){
    let target_analysis = [];
    for(let i = 0; i<selectedKGs.length; i++){
        for(let j = 0; j<quality_data.length; j++){
            if(selectedKGs[i].id === quality_data[j].kg_id && quality_data[j].analysis_date === analysis_date){
                target_analysis.push(quality_data[j])
            }
        }
    }

    return target_analysis;
}

function trasform_to_series_stacked(quality_data,selectedKGs,quality_dimension,quality_metrics, quality_metrics_label){
    let series = []
    for(let i = 0; i< quality_metrics.length; i++){
        let serie = {
            name: quality_metrics_label[i],
            data : [],
            minPointLength: 10,
        }
        for(let j = 0; j < quality_data.length; j++){
            let quality_category_array = quality_data[j].Quality_category_array;
            serie.data.push(parseFloat(quality_category_array[quality_dimension][quality_metrics[i]]))
        }
        series.push(serie);
    }
    return series
}

function remove_duplicates(arr){
    return arr.filter((item,index) => arr.indexOf(item) === index);
}

function series_for_polar_chart(analysis_selected,selectedKGs,quality_dimension){
    let series = [];
    for(let i = 0; i<selectedKGs.length; i++){
        let serie = {
            name : '',
            data: [],
        };
        for(let j = 0; j<analysis_selected.length; j++){
            if(selectedKGs[i].id === analysis_selected[j].kg_id){
                const consistency_obj = analysis_selected[j].Quality_category_array[quality_dimension];
                serie.data = [parseFloat(consistency_obj.deprecated),parseFloat(consistency_obj.triplesMC),parseFloat(consistency_obj.triplesMP),parseFloat(consistency_obj.undefinedClass),parseFloat(consistency_obj.undefinedProperties)];
                serie.name = analysis_selected[j].kg_name;
            }
        }
        series.push(serie);
    }

    return series
}

function trasform_to_series_conc(quality_data,selectedKGs,quality_dimension,quality_metric,custom_series_name,min_point){
    let series = []
    for(let i = 0; i< selectedKGs.length; i++){
        if(min_point){
            let serie = {
                name: custom_series_name,
                data : [],
                minPointLength: 10,
            }
            series.push(serie)
        }
        else{
            let serie = {
                name: custom_series_name,
                data : [],
                minPointLength: 10,
            }
            series.push(serie)
        }
    }
    for(let i = 0; i < quality_data.length; i++){
        for(let j = 0; j<selectedKGs.length; j++){
            if (selectedKGs[j].id === quality_data[i].kg_id){
                const tab_date = quality_data[i].analysis_date.split('-');
                const date_utc = Date.UTC(parseInt(tab_date[0]),parseInt(tab_date[1])-1,parseInt(tab_date[2]));
                series[j].data.push([date_utc,parseFloat(quality_data[i].Quality_category_array[quality_dimension][quality_metric])])
            }
        }
    }
    return series
}

function trasform_history_data(quality_data,selectedKGs){
    let series = []
    for(let i = 0; i< selectedKGs.length; i++){
        let serie = {
            name: '',
            data : [],
        }
        series.push(serie)
    }
    for(let i = 0; i < quality_data.length; i++){
        for(let j = 0; j<selectedKGs.length; j++){
            if (selectedKGs[j].id === quality_data[i].kg_id){
                const historical_up = quality_data[i].Quality_category_array['Currency'].historicalUp;
                const historical_up_arr = historical_up.split(';')
                const data = historical_up_arr.map((item) =>{
                    const date = item.split('|')[0];
                    const triples_modified = item.split('|')[1];
                    const tab_date = date.split('-');
                    const date_utc = Date.UTC(parseInt(tab_date[0]),parseInt(tab_date[1])-1,parseInt(tab_date[2]));
                    const data = [date_utc,parseInt(triples_modified)]  
                    
                    return data
                });
                series[j].data = data
                if(series[j].name === '' || series[j].name === undefined)
                    series[j].name = quality_data[i].kg_name;
            }
        }
    }
    return series
}

function trasform_to_series_compl(quality_data,selectedKGs,quality_dimension,quality_metric,custom_series_name){
    let series = []
    for(let i = 0; i< selectedKGs.length; i++){
        let serie = {
            name: custom_series_name,
            data : [],
        }
        series.push(serie)
    }
    for(let i = 0; i < quality_data.length; i++){
        for(let j = 0; j<selectedKGs.length; j++){
            if (selectedKGs[j].id === quality_data[i].kg_id){
                const tab_date = quality_data[i].analysis_date.split('-');
                const date_utc = Date.UTC(parseInt(tab_date[0]),parseInt(tab_date[1])-1,parseInt(tab_date[2]));
                series[j].data.push([date_utc,parseFloat(quality_data[i].Quality_category_array[quality_dimension][quality_metric])])
                if(series[j].stack === '')
                    series[j].stack = quality_data[i].kg_name;
                if(series[j].name === '' || series[j].name === undefined)
                    series[j].name = quality_data[i].kg_name;
            }
        }
    }
    return series
}

function trasform_rep_conc_to_series(quality_data,selectedKGs,quality_dimension,min,perc25,median,perc75,max,series_name){
    let series = []
    for(let i = 0; i< selectedKGs.length; i++){
        let serie = {
            id : selectedKGs[i].id,
            name: series_name,
            data : []
        }
        series.push(serie)
    }
    for(let i = 0; i < quality_data.length; i++){
        for(let j = 0; j<selectedKGs.length; j++){
            if (series[j].id === quality_data[i].kg_id){
                const tab_date = quality_data[i].analysis_date.split('-');
                const date_utc = Date.UTC(parseInt(tab_date[0]),parseInt(tab_date[1])-1,parseInt(tab_date[2]));
                const  dimension_obj =  quality_data[i].Quality_category_array[quality_dimension]
                series[j].data.push([date_utc,parseFloat(dimension_obj[min]),parseFloat(dimension_obj[perc25]),parseFloat(dimension_obj[median]),parseFloat(dimension_obj[perc75]),parseFloat(dimension_obj[max])])
            }
        }
    }
    return series
}

function trasform_rep_conc_to_series_multiple(quality_data,selectedKGs,quality_dimension,min,perc25,median,perc75,max,series_name){
    let series = []
    for(let i = 0; i< selectedKGs.length; i++){
        let serie = {
            id : selectedKGs[i].id,
            name: series_name,
            data : []
        }
        series.push(serie)
    }
    for(let i = 0; i < quality_data.length; i++){
        for(let j = 0; j<selectedKGs.length; j++){
            if (series[j].id === quality_data[i].kg_id){
                const tab_date = quality_data[i].analysis_date.split('-');
                const date_utc = Date.UTC(parseInt(tab_date[0]),parseInt(tab_date[1])-1,parseInt(tab_date[2]));
                const  dimension_obj =  quality_data[i].Quality_category_array[quality_dimension]
                series[j].data.push([date_utc,parseFloat(dimension_obj[min]),parseFloat(dimension_obj[perc25]),parseFloat(dimension_obj[median]),parseFloat(dimension_obj[perc75]),parseFloat(dimension_obj[max])])
                if(series[j].name === '' || series[j].name === undefined)
                    series[j].name = quality_data[i].kg_name;
            }
        }
    }
    return series
}

function create_percentage_label_series(underst_data,amount_data,selectedKGs){
    let series = [];
    for(let i = 0; i<selectedKGs.length; i++){
        let serie = {
            name: '',
            data : []
        }
        series.push(serie)
    }
        for(let j = 0; j < selectedKGs.length; j++){
            for(let k = 0; k < underst_data.length; k++){
                if(underst_data[k].kg_id === selectedKGs[j].id){
                    const analysis_date = underst_data[k].analysis_date;
                    for(let i = 0; i<amount_data.length; i++){
                        if(underst_data[k].kg_id === amount_data[i].kg_id && analysis_date === amount_data[i].analysis_date){
                            const num_triples = parseInt(amount_data[i].Quality_category_array['Amount of data'].numTriples_merged);
                            const num_label = parseInt(underst_data[k].Quality_category_array['Understandability'].numLabel);
                            const percentage = num_label/num_triples * 100;
                            const tab_date = underst_data[k].analysis_date.split('-');
                            const date_utc = Date.UTC(parseInt(tab_date[0]),parseInt(tab_date[1])-1,parseInt(tab_date[2]));
                            series[j].data.push([date_utc,parseFloat(percentage.toFixed(2))]);
                            if(series[j].name === '')
                                series[j].name = underst_data[k].kg_name 
                        }
                    }
                }
            }
        }
    return series;
}

function extract_most_recent(quality_data,selectedKGs){
    let last_analysis = []
    for(let i = 0; i<selectedKGs.length; i++){
        const last_analysis_date = quality_data[quality_data.length -1].analysis_date;
        for(let j = 0; j<quality_data.length; j++){
            if(selectedKGs[i].id === quality_data[j].kg_id && last_analysis_date === quality_data[j].analysis_date){
                last_analysis.push(quality_data[j])
            }
        }
    }
    return last_analysis;
}

function add_believability_and_amount(under_data,believability_data,amount_data,selectedKGs){
    for(let i = 0; i<under_data.length; i++){
        for(let j = 0; j<believability_data.length; j++){
            if(under_data[i].kg_id === believability_data[j].kg_id){
                let quality_obj = under_data[i].Quality_category_array['Understandability'];
                quality_obj['title'] = believability_data[j].Quality_category_array['Believability'].title;
                quality_obj['description'] = believability_data[j].Quality_category_array['Believability'].description;
                quality_obj['URI'] = believability_data[j].Quality_category_array['Believability'].URI;
            }
        }
        for(let k = 0; k<amount_data.length;k++){
            if(under_data[i].kg_id === amount_data[k].kg_id && under_data[i].analysis_date === amount_data[k].analysis_date){
                let quality_obj = under_data[i].Quality_category_array['Understandability'];
                quality_obj['numTriples_merged'] = amount_data[k].Quality_category_array['Amount of data'].numTriples_merged;
            }
        }
    }
    return under_data
}

function add_amount(interp_data,amount_data,selectedKGs){
    for(let i = 0; i<interp_data.length; i++){
        for(let k = 0; k<amount_data.length;k++){
            if(interp_data[i].kg_id === amount_data[k].kg_id && interp_data[i].analysis_date === amount_data[k].analysis_date){
                let quality_obj = interp_data[i].Quality_category_array['Interpretability'];
                quality_obj['numTriples_merged'] = amount_data[k].Quality_category_array['Amount of data'].numTriples_merged;
            }
        }
    }
    return interp_data
}

function set_message_availability(versatilityData){
    for(let i = 0; i<versatilityData.length; i++){
        let sparql = versatilityData[i].Quality_category_array['Versatility'].sparqlEndpoint;
        let rdf = versatilityData[i].Quality_category_array['Versatility'].availabilityRDFD_merged;
        if(sparql === '1')
            sparql = 'Link online'
        else if(sparql === '-1')
            sparql = 'No link available'
        else if(sparql === '0')
            sparql = 'Link offline'
        if(rdf === '1')
            rdf = 'Link online'
        else if(rdf === '-1')
            rdf = 'No link available'
        else if(rdf === '0')
            rdf = 'Link offline'
        versatilityData[i].Quality_category_array['Versatility'].sparqlEndpoint = sparql;
        versatilityData[i].Quality_category_array['Versatility'].availabilityRDFD_merged = rdf;
    }
}

function score_to_series(quality_data,selectedKGs,quality_dimension,quality_metric,custom_series_name,max_score){
    let series = []
    for(let i = 0; i< selectedKGs.length; i++){
        let serie = {
            name: custom_series_name,
            data : [],
        }
        series.push(serie)
    }
    for(let i = 0; i < quality_data.length; i++){
        for(let j = 0; j<selectedKGs.length; j++){
            if (selectedKGs[j].id === quality_data[i].kg_id){
                const tab_date = quality_data[i].analysis_date.split('-');
                const date_utc = Date.UTC(parseInt(tab_date[0]),parseInt(tab_date[1])-1,parseInt(tab_date[2]));
                const score_value = parseFloat(quality_data[i][quality_dimension][quality_metric])
                const normalized_score = parseFloat(((score_value/max_score) * 100).toFixed(2));
                series[j].data.push([date_utc,normalized_score]);
            }
        }
    }
    return series
}

function score_series_multiple_kgs(quality_data,selectedKGs,max_score){
    let data = [];
    for(let i = 0; i<selectedKGs.length; i++){
        for(let j = 0; j< quality_data.length; j++){
            if(selectedKGs[i].id === quality_data[j].kg_id){
                const score_value = parseFloat(quality_data[i]['Score']['totalScore'])
                const normalized_score = parseFloat(((score_value/max_score) * 100).toFixed(2));
                const row_data = {
                    kgname : quality_data[j].kg_name,
                    score : normalized_score
                }
                data.push(row_data);
            }
        }
    }
    return data
}

function score_for_dimension_kgs(score_data,max_score){
    let data = [];
    for(let i = 0; i<score_data.length; i++){
        const score_value = parseFloat(score_data[i]['Score']['totalScore'])
        const normalized_score = parseFloat(((score_value/max_score) * 100).toFixed(2));
        const row_data = {
            kgname : score_data[i].kg_name,
            score : normalized_score,
            availability : score_data[i]['Score']['availabilityScoreValue'],
            licensing : score_data[i]['Score']['availabilityScoreValue'],
            interlinking : score_data[i]['Score']['interlinkingScoreValue'],
            performance : score_data[i]['Score']['performanceScoreValue'],
            accuracy : score_data[i]['Score']['accuracyScoreValue'],
            consistency : score_data[i]['Score']['consistencyScoreValue'],
            conciseness : score_data[i]['Score']['concisenessScoreValue'],
            verifiability : score_data[i]['Score']['verifiabilityScoreValue'],
            reputation : score_data[i]['Score']['reputationScoreValue'],
            believability : score_data[i]['Score']['believabilityScoreValue'],
            currency : score_data[i]['Score']['currencyScoreValue'],
            volatility : score_data[i]['Score']['volatilityScoreValue'],
            completeness : score_data[i]['Score']['completenessScoreValue'],
            amount : score_data[i]['Score']['amountScoreValue'],
            repCons : score_data[i]['Score']['repConsScoreValue'],
            repConc : score_data[i]['Score']['repConcScoreValue'],
            understandability : score_data[i]['Score']['understScoreValue'],
            interpretability : score_data[i]['Score']['interpretabilityScoreValue'],
            versatility : score_data[i]['Score']['versatilityScoreValue'],
            security : score_data[i]['Score']['securityScoreValue'],
        }
        data.push(row_data);
    }
    return data
}

function initialize_score_map(){
    let score_map = {
        'availability' : "1",
        'licensing' : "1",
        'interlinking' : "1",
        'security' : "1",
        'performance' : "1",
        'accuracy' : "1",
        'consistency' : "1",
        'conciseness' : "1",
        'reputation' : "1",
        'believability' : "1",
        'verifiability' : "1",
        'currency' : "1",
        'volatility' : "1",
        'completeness' :"1",
        'amount' : "1",
        'repConc' : "1",
        'repCons' : "1",
        'under' : "1",
        'interp' : "1",
        'vers': "1"
    }
    return score_map
}

function recalculate_score(score_data,selectedKGs,score_weights,dimension_number){
    const personalized_score = JSON.parse(JSON.stringify(score_data));
    
    for(let i = 0; i<selectedKGs.length; i++){
        for(let j = 0; j<personalized_score.length; j++){
            const score_obj = personalized_score[j]['Score']
            for(let key_weights in score_weights){
                for(let key_score in score_obj){
                    if(key_score.includes(key_weights)){
                        const weight = parseFloat(score_weights[key_weights])
                        score_obj[key_score] *= weight 
                        break;
                        }
                    }
                }
            }
        }

    for(let i = 0; i<personalized_score.length; i++){
        let sum_score = 0;
        for(let key in personalized_score[i]['Score']){
            if(key !== 'normalizedScore' && key !== 'totalScore' && key !== 'dimensionNumber')
                sum_score += personalized_score[i]['Score'][key];
        }
        //for old data we have 0 because we doesn't have the single score from every quality dimension
        personalized_score[i]['Score']['normalizedScore'] = (sum_score / dimension_number) * 100;
        personalized_score[i]['Score']['totalScore'] = sum_score / dimension_number;
    }

    return personalized_score
}

function get_selected_dimension(dimensions_map){
    let selected_dimensions = [];
    for(let key in dimensions_map){
        if(parseFloat(dimensions_map[key]) > 0){
            if(key === 'repConc')
                selected_dimensions.push('representational-conciseness');
            else if(key === 'rep-cons')
                selected_dimensions.push('representational-consistency');
            else if(key === 'under')
                selected_dimensions.push('understandability');
            else if(key === 'interp')
                selected_dimensions.push('interpretability');
            else if(key === 'vers')
                selected_dimensions.push('versatility');
            else
                selected_dimensions.push(key)
        }
    }
    return selected_dimensions
}

function convert_analysis_date(analysis_date_obj){
    const date_list = analysis_date_obj.map(obj => obj.analysis_date);
    const date_list_sorted = [...date_list].sort()
    let parsed_date = []
    for(let i = 0; i<date_list_sorted.length; i++){
        parsed_date.push(parseISO(date_list_sorted[i]))
    }   
    return parsed_date
}

function compare_date(date_a, date_b){
    return new Date(date_a.analysis_date) - new Date(date_b.analysis_date);
}

function compare_date_array(date_a, date_b){
    return date_b[0] - date_b[0];
}

export {trasform_to_series,compact_temporal_data, trasform_latency_to_series, trasform_throughput_to_series, get_analysis_date, find_target_analysis,trasform_to_series_stacked, remove_duplicates, series_for_polar_chart, trasform_to_series_conc, trasform_history_data, trasform_to_series_compl, trasform_rep_conc_to_series, trasform_rep_conc_to_series_multiple, create_percentage_label_series,extract_most_recent,add_believability_and_amount,add_amount,set_message_availability,score_to_series, score_series_multiple_kgs, recalculate_score, initialize_score_map, get_selected_dimension,score_for_dimension_kgs, convert_analysis_date,trasform_to_series_sparql_av,compact_string_temporal_data, compare_date, compare_date_array};