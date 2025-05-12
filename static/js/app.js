$(document).ready(function() {
    let selectedTickers = [];
    let currentTicker = null;
    
    // Handle stock selection
    $('.stock-button').click(function() {
        const ticker = $(this).data('ticker');
        
        // Toggle selection for comparison
        if ($(this).hasClass('active')) {
            $(this).removeClass('active');
            selectedTickers = selectedTickers.filter(t => t !== ticker);
        } else {
            $(this).addClass('active');
            if (!selectedTickers.includes(ticker)) {
                selectedTickers.push(ticker);
            }
        }
        
        // Update current ticker and fetch data
        currentTicker = ticker;
        fetchStockData(ticker);
    });
    
    // Period selection change
    $('#period-selector').change(function() {
        if (currentTicker) {
            fetchStockData(currentTicker);
        }
    });
    
    // Compare button click
    $('#compare-button').click(function() {
        if (selectedTickers.length > 0) {
            compareStocks(selectedTickers);
        } else {
            alert('Please select at least one stock to compare');
        }
    });
    
    // Fetch stock data function
    function fetchStockData(ticker) {
        // Show loading indicator
        $('#stock-placeholder').addClass('d-none');
        $('#comparison-chart').addClass('d-none');
        $('#stock-details').addClass('d-none');
        $('#loading-indicator').removeClass('d-none');
        
        // Get selected period
        const period = $('#period-selector').val();
        
        // Make AJAX request
        $.ajax({
            url: '/get_stock_data',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                ticker: ticker,
                period: period
            }),
            success: function(response) {
                // Hide loading indicator
                $('#loading-indicator').addClass('d-none');
                
                // Update company information
                $('#company-name').text(response.company_name);
                $('#current-price').text('$' + response.current_price);
                
                // Update percent change with proper styling
                const percentChange = response.percent_change;
                let badgeClass = 'neutral';
                let prefix = '';
                
                if (percentChange > 0) {
                    badgeClass = 'positive';
                    prefix = '+';
                } else if (percentChange < 0) {
                    badgeClass = 'negative';
                }
                
                $('#percent-change')
                    .text(prefix + percentChange + '%')
                    .removeClass('positive negative neutral')
                    .addClass(badgeClass);
                
                // Create the chart
                const plotData = JSON.parse(response.plot);
                Plotly.newPlot('stock-chart', plotData.data, plotData.layout);
                
                // Show the stock details
                $('#stock-details').removeClass('d-none');
            },
            error: function(error) {
                // Hide loading indicator
                $('#loading-indicator').addClass('d-none');
                
                // Show error message
                $('#stock-placeholder').removeClass('d-none')
                    .html('<div class="alert alert-danger">Error loading stock data: ' + 
                          (error.responseJSON ? error.responseJSON.error : 'Unknown error') + '</div>');
            }
        });
    }
    
    // Compare stocks function
    function compareStocks(tickers) {
        // Show loading indicator
        $('#stock-placeholder').addClass('d-none');
        $('#stock-details').addClass('d-none');
        $('#comparison-chart').addClass('d-none');
        $('#loading-indicator').removeClass('d-none');
        
        // Get selected period
        const period = $('#period-selector').val();
        
        // Make AJAX request
        $.ajax({
            url: '/compare',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                tickers: tickers,
                period: period
            }),
            success: function(response) {
                // Hide loading indicator
                $('#loading-indicator').addClass('d-none');
                
                // Create the chart
                const plotData = JSON.parse(response.plot);
                Plotly.newPlot('comparison-chart', plotData.data, plotData.layout);
                
                // Show the comparison chart
                $('#comparison-chart').removeClass('d-none');
            },
            error: function(error) {
                // Hide loading indicator
                $('#loading-indicator').addClass('d-none');
                
                // Show error message
                $('#stock-placeholder').removeClass('d-none')
                    .html('<div class="alert alert-danger">Error comparing stocks: ' + 
                          (error.responseJSON ? error.responseJSON.error : 'Unknown error') + '</div>');
            }
        });
    }
}); 