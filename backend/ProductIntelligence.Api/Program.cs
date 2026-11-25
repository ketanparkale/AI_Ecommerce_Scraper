using Microsoft.EntityFrameworkCore;
using ProductIntelligence.Infrastructure.Data;
using ProductIntelligence.Core.Products.Interfaces;
using ProductIntelligence.Infrastructure.Repositories;
using ProductIntelligence.Core.Products.Services;
using ProductIntelligence.Core.Common;
using ProductIntelligence.Infrastructure.Scraping;
using ProductIntelligence.Core.Watches.Services;
using ProductIntelligence.Core.Notifications.Interfaces;
using ProductIntelligence.Infrastructure.Notifications.Repositories;
using ProductIntelligence.Core.Notifications.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.

builder.Services.AddOpenApi();
var connectionString = builder.Configuration
    .GetConnectionString("DefaultConnection");

builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(connectionString));
builder.Services.AddScoped<IProductRepository, ProductRepository>();
builder.Services.AddScoped<IProductSnapshotRepository, ProductSnapshotRepository>();
builder.Services.AddScoped<IProductVariantRepository, ProductVariantRepository>();
builder.Services.AddScoped<IProductPriceHistoryRepository, ProductPriceHistoryRepository>();
builder.Services.AddScoped<ProductService>();
builder.Services.AddScoped<IUnitOfWork, UnitOfWork>();
builder.Services.AddScoped<ProductMonitoringService>();
builder.Services.AddScoped<IProductWatchRepository,ProductWatchRepository>();
builder.Services.AddScoped<WatchEvaluationService>();
builder.Services.AddScoped<NotificationService>();
builder.Services.AddScoped<INotificationRepository,NotificationRepository>();
builder.Services.AddScoped<ProductWatchService>();
builder.Services.AddScoped<IProductWatchRepository,ProductWatchRepository>();

builder.Services.AddHttpClient<IProductScraperClient, ProductScraperClient>(
    client =>
    {
        client.BaseAddress = new Uri("http://localhost:8000/");
        client.Timeout = TimeSpan.FromSeconds(150);
    }
);


builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.MapControllers();
app.Run();

