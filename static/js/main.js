// Global variables
let orderBookData = {};
let marketData = {};
let marketDataInterval = null; // Add this global variable

// Document ready function
$(document).ready(function() {
    // Initialize event handlers
    initializeFormHandlers();
    initializeSymbolChange();
});

// Initialize form handlers
function initializeFormHandlers() {
    // Order type change handler
    $('#orderType').on('change', function() {
        const orderType = $(this).val();
        
        // Hide all order-specific fields first
        $('.order-param').hide();
        
        // Show relevant fields based on order type
        switch(orderType) {
            case 'LIMIT':
                $('#priceField').show();
                break;
            case 'STOP':
                $('#stopPriceField').show();
                $('#priceField').show(); // Show limit price for STOP
                break;
            case 'STOP_MARKET':
                $('#stopPriceField').show();
                break;
        }
    });
    
    // Order form submission
    $('#orderForm').on('submit', function(e) {
        e.preventDefault();
        
        // Show loading state
        const submitBtn = $('#placeOrderBtn');
        const originalText = submitBtn.text();
        submitBtn.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...');
        submitBtn.prop('disabled', true);
        
        // Gather form data
        const symbol = $('#symbol').val();
        const side = $('input[name="side"]:checked').val();
        const orderType = $('#orderType').val();
        const quantity = $('#quantity').val();
        
        let requestData = {
            symbol: symbol,
            side: side,
            order_type: orderType,
            quantity: quantity
        };
        
        // Add order type specific parameters
        if (orderType === 'LIMIT') {
            requestData.price = $('#price').val();
        }
        
        if (orderType === 'STOP') {
            requestData.stop_price = $('#stopPrice').val();
            requestData.price = $('#price').val(); // Add limit price for STOP
        }
        
        if (orderType === 'STOP_MARKET') {
            requestData.stop_price = $('#stopPrice').val();
        }
        
        // Send request to place order
        $.ajax({
            url: '/api/place-order',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(requestData),
            success: function(response) {
                // Display success message
                showOrderStatus(response, true);
                
                // Reset form
                $('#orderForm')[0].reset();
                
                // Refresh order history
                loadOrderHistory();
                loadOpenOrders();
                loadAccountBalance();
            },
            error: function(xhr) {
                let errorMsg = 'Failed to place order';
                
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                
                // Display error message
                showOrderStatus({ error: errorMsg }, false);
            },
            complete: function() {
                // Reset button state
                submitBtn.html(originalText);
                submitBtn.prop('disabled', false);
            }
        });
    });
    
    // Cancel order buttons
    $(document).on('click', '.cancel-order-btn', function() {
        const orderId = $(this).data('order-id');
        const symbol = $(this).data('symbol');
        
        if (confirm('Are you sure you want to cancel this order?')) {
            $.ajax({
                url: '/api/cancel-order',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    symbol: symbol,
                    order_id: orderId
                }),
                success: function(response) {
                    alert('Order cancelled successfully');
                    
                    // Refresh order lists
                    loadOpenOrders();
                    loadOrderHistory();
                },
                error: function(xhr) {
                    let errorMsg = 'Failed to cancel order';
                    
                    if (xhr.responseJSON && xhr.responseJSON.error) {
                        errorMsg = xhr.responseJSON.error;
                    }
                    
                    alert('Error: ' + errorMsg);
                }
            });
        }
    });
}

// Initialize symbol change handler
function initializeSymbolChange() {
    $('#symbol').on('change', function() {
        const symbol = $(this).val();

        // Clear any previous interval
        if (marketDataInterval) {
            clearInterval(marketDataInterval);
            marketDataInterval = null;
        }

        if (symbol) {
            // Show market data container
            $('#marketDataContainer').show();

            // Load market data for the selected symbol
            fetchAndUpdateMarketData(symbol);
        } else {
            // Hide market data container
            $('#marketDataContainer').hide();
        }
    });
    // Add manual refresh button handler
    $(document).on('click', '#refreshMarketData', function() {
        const symbol = $('#symbol').val();
        if (symbol) {
            fetchAndUpdateMarketData(symbol);
        }
    });
}

// Helper function to fetch and update market data for a symbol
function fetchAndUpdateMarketData(symbol) {
    $.ajax({
        url: '/api/market-data',
        type: 'GET',
        data: { symbol: symbol },
        success: function(response) {
            marketData = response;
            updateMarketDataUI(response);
        },
        error: function(xhr) {
            console.error('Failed to load market data', xhr);
        }
    });
}

// Update market data UI
function updateMarketDataUI(data) {
    if (!data) return;
    
    // Format price
    const price = parseFloat(data.price || data.lastPrice);
    const formattedPrice = `$${price.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    })}`;
    
    // Calculate price change
    const priceChange = parseFloat(data.priceChangePercent);
    const priceChangeClass = priceChange >= 0 ? 'text-success' : 'text-danger';
    const priceChangeArrow = priceChange >= 0 ? '↑' : '↓';
    const formattedChange = `${priceChangeArrow} ${Math.abs(priceChange).toFixed(2)}%`;
    
    // Update UI elements
    $('#currentPrice').text(formattedPrice);
    $('#priceChange').text(formattedChange);
    $('#priceChange').removeClass('text-success text-danger').addClass(priceChangeClass);
}

// Load order history
function loadOrderHistory() {
    $.ajax({
        url: '/api/orders',
        type: 'GET',
        success: function(response) {
            if (Array.isArray(response)) {
                updateOrderHistoryTable(response);
            } else {
                console.error('Invalid order history response', response);
            }
        },
        error: function(xhr) {
            console.error('Failed to load order history', xhr);
            $('#allOrdersTableBody').html('<tr><td colspan="8" class="text-center text-danger">Failed to load orders</td></tr>');
        }
    });
}

// Load open orders
function loadOpenOrders() {
    $.ajax({
        url: '/api/open-orders',
        type: 'GET',
        success: function(response) {
            if (Array.isArray(response)) {
                updateOpenOrdersTable(response);
            } else {
                console.error('Invalid open orders response', response);
            }
        },
        error: function(xhr) {
            console.error('Failed to load open orders', xhr);
            $('#openOrdersTableBody').html('<tr><td colspan="8" class="text-center text-danger">Failed to load open orders</td></tr>');
        }
    });
}

// Load account balance
function loadAccountBalance() {
    $.ajax({
        url: '/api/account',
        type: 'GET',
        success: function(response) {
            updateAccountBalanceTable(response);
        },
        error: function(xhr) {
            console.error('Failed to load account balance', xhr);
            $('#accountBalanceTableBody').html('<tr><td colspan="4" class="text-center text-danger">Failed to load balance data</td></tr>');
        }
    });
}

// Update order history table
function updateOrderHistoryTable(orders) {
    const allOrdersTable = $('#allOrdersTableBody');
    const filledOrdersTable = $('#filledOrdersTableBody');
    
    // Sort orders by time (newest first)
    orders.sort((a, b) => b.time - a.time);
    
    if (orders.length === 0) {
        allOrdersTable.html('<tr><td colspan="8" class="text-center">No orders found</td></tr>');
        filledOrdersTable.html('<tr><td colspan="7" class="text-center">No filled orders found</td></tr>');
        return;
    }
    
    // Clear tables
    allOrdersTable.empty();
    filledOrdersTable.empty();
    
    // Filter filled orders
    const filledOrders = orders.filter(order => order.status === 'FILLED');
    
    // Update all orders table
    orders.forEach(order => {
        const row = createOrderRow(order, true);
        allOrdersTable.append(row);
    });
    
    // Update filled orders table
    if (filledOrders.length === 0) {
        filledOrdersTable.html('<tr><td colspan="7" class="text-center">No filled orders found</td></tr>');
    } else {
        filledOrders.forEach(order => {
            const row = createOrderRow(order, false);
            filledOrdersTable.append(row);
        });
    }
}

// Update open orders table
function updateOpenOrdersTable(orders) {
    const openOrdersTable = $('#openOrdersTableBody');
    
    if (orders.length === 0) {
        openOrdersTable.html('<tr><td colspan="8" class="text-center">No open orders</td></tr>');
        return;
    }
    
    // Sort orders by time (newest first)
    orders.sort((a, b) => b.time - a.time);
    
    // Clear table
    openOrdersTable.empty();
    
    // Add rows
    orders.forEach(order => {
        const row = createOrderRow(order, true);
        openOrdersTable.append(row);
    });
}

// Create order row HTML
function createOrderRow(order, showActions) {
    // Format time
    const orderTime = new Date(order.time);
    const formattedTime = orderTime.toLocaleString();
    
    // Format price
    const price = parseFloat(order.price);
    const formattedPrice = price > 0 ? `$${price.toFixed(2)}` : 'Market';
    
    // Format stop price
    const stopPrice = parseFloat(order.stopPrice);
    const formattedStopPrice = stopPrice > 0 ? `$${stopPrice.toFixed(2)}` : '-';

    // Format quantity
    const quantity = parseFloat(order.origQty);
    const formattedQuantity = quantity.toFixed(4);
    
    // Create status badge
    let statusBadgeClass = 'bg-secondary';
    
    switch(order.status) {
        case 'FILLED':
            statusBadgeClass = 'bg-success';
            break;
        case 'CANCELED':
        case 'REJECTED':
        case 'EXPIRED':
            statusBadgeClass = 'bg-danger';
            break;
        case 'NEW':
        case 'PARTIALLY_FILLED':
            statusBadgeClass = 'bg-primary';
            break;
    }
    
    // Create side badge
    const sideBadgeClass = order.side === 'BUY' ? 'bg-success' : 'bg-danger';
    
    // Create action buttons
    let actionButtons = '';
    
    if (showActions && (order.status === 'NEW' || order.status === 'PARTIALLY_FILLED')) {
        actionButtons = `
            <button class="btn btn-sm btn-danger cancel-order-btn" 
                    data-order-id="${order.orderId}" 
                    data-symbol="${order.symbol}">
                Cancel
            </button>
        `;
    }
    
    // Create table row
    const row = `
        <tr>
            <td>${order.symbol}</td>
            <td><span class="badge ${sideBadgeClass}">${order.side}</span></td>
            <td>${order.type}</td>
            <td>${formattedPrice}</td>
            <td>${formattedStopPrice}</td>
            <td>${formattedQuantity}</td>
            <td><span class="badge ${statusBadgeClass}">${order.status}</span></td>
            <td>${formattedTime}</td>
            ${showActions ? `<td>${actionButtons}</td>` : ''}
        </tr>
    `;
    
    return row;
}

// Update account balance table
function updateAccountBalanceTable(accountInfo) {
    const balanceTable = $('#accountBalanceTableBody');
    
    if (!accountInfo || !accountInfo.assets || accountInfo.assets.length === 0) {
        balanceTable.html('<tr><td colspan="4" class="text-center">No balance data available</td></tr>');
        return;
    }
    
    // Clear table
    balanceTable.empty();
    
    // Filter assets with balance > 0
    const assets = accountInfo.assets.filter(asset => parseFloat(asset.walletBalance) > 0);
    
    if (assets.length === 0) {
        balanceTable.html('<tr><td colspan="4" class="text-center">No assets with balance</td></tr>');
        return;
    }
    
    // Add rows
    assets.forEach(asset => {
        const walletBalance = parseFloat(asset.walletBalance);
        const unrealizedProfit = parseFloat(asset.unrealizedProfit);
        const availableBalance = parseFloat(asset.availableBalance);
        
        const row = `
            <tr>
                <td>${asset.asset}</td>
                <td>${walletBalance.toFixed(2)}</td>
                <td class="${unrealizedProfit >= 0 ? 'text-success' : 'text-danger'}">
                    ${unrealizedProfit.toFixed(2)}
                </td>
                <td>${availableBalance.toFixed(2)}</td>
            </tr>
        `;
        
        balanceTable.append(row);
    });
}

// Show order status modal
function showOrderStatus(response, success) {
    const modalBody = $('#orderStatusBody');
    
    if (success) {
        // Format order details for success message
        const stopPrice = response.stopPrice ? '$' + parseFloat(response.stopPrice).toFixed(2) : '-';
        const price = response.price ? '$' + parseFloat(response.price).toFixed(2) : 'Market';
        const orderDetails = `
            <div class="text-center mb-3">
                <i class="fas fa-check-circle fa-3x text-success"></i>
            </div>
            <h5 class="text-center mb-3">Order Placed Successfully</h5>
            <div class="table-responsive">
                <table class="table">
                    <tr>
                        <th>Symbol:</th>
                        <td>${response.symbol}</td>
                    </tr>
                    <tr>
                        <th>Order ID:</th>
                        <td>${response.orderId}</td>
                    </tr>
                    <tr>
                        <th>Side:</th>
                        <td><span class="badge ${response.side === 'BUY' ? 'bg-success' : 'bg-danger'}">${response.side}</span></td>
                    </tr>
                    <tr>
                        <th>Type:</th>
                        <td>${response.type}</td>
                    </tr>
                    <tr>
                        <th>Price:</th>
                        <td>${price}</td>
                    </tr>
                    <tr>
                        <th>Stop Price:</th>
                        <td>${stopPrice}</td>
                    </tr>
                    <tr>
                        <th>Quantity:</th>
                        <td>${parseFloat(response.origQty).toFixed(4)}</td>
                    </tr>
                    <tr>
                        <th>Status:</th>
                        <td><span class="badge bg-primary">${response.status}</span></td>
                    </tr>
                </table>
            </div>
        `;
        
        modalBody.html(orderDetails);
    } else {
        // Format error message
        const errorMsg = `
            <div class="text-center mb-3">
                <i class="fas fa-exclamation-circle fa-3x text-danger"></i>
            </div>
            <h5 class="text-center mb-3">Order Failed</h5>
            <div class="alert alert-danger">
                ${response.error || 'An unknown error occurred'}
            </div>
        `;
        
        modalBody.html(errorMsg);
    }
    
    // Show the modal
    new bootstrap.Modal(document.getElementById('orderStatusModal')).show();
}

// Refresh all data
function refreshData() {
    // Get selected symbol
    const symbol = $('#symbol').val();
    
    // Refresh market data if symbol is selected
    if (symbol) {
        $.ajax({
            url: '/api/market-data',
            type: 'GET',
            data: { symbol: symbol },
            success: function(response) {
                marketData = response;
                updateMarketDataUI(response);
            }
        });
    }
    
    // Refresh order history and account balance
    loadOrderHistory();
    loadOpenOrders();
    loadAccountBalance();
}