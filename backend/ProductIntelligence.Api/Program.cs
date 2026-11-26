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
using ProductIntelligence.Infrastructure.BackgroundServices;
using Microsoft.AspNetCore.Identity;
using ProductIntelligence.Infrastructure.Identity;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using ProductIntelligence.Api.Services;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi;
using System.Text;
using DotNetEnv;

var currentDirectory = Directory.GetCurrentDirectory();

var envPath = Path.GetFullPath(
    Path.Combine(currentDirectory, "..", "..", ".env")
);

Env.Load(envPath);

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.

builder.Services.AddOpenApi();
var connectionString = builder.Configuration
    .GetConnectionString("DefaultConnection");

builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(connectionString));

builder.Services
    .AddIdentityCore<ApplicationUser>(options =>
    {
        // User settings
        options.User.RequireUniqueEmail = true;

        // Password settings
        options.Password.RequiredLength = 8;
        options.Password.RequireDigit = true;
        options.Password.RequireUppercase = true;
        options.Password.RequireLowercase = true;
        options.Password.RequireNonAlphanumeric = false;

        // Account settings
        options.Lockout.MaxFailedAccessAttempts = 5;
        options.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(15);
    })
    .AddRoles<IdentityRole<Guid>>()
    .AddEntityFrameworkStores<ApplicationDbContext>()
    .AddSignInManager();

var secretKey = Environment.GetEnvironmentVariable("JWT_SECRET_KEY")
    ?? throw new InvalidOperationException("JWT secret is missing.");

var key = Encoding.UTF8.GetBytes(secretKey);

var jwtSettings = builder.Configuration.GetSection("Jwt");

builder.Services
    .AddAuthentication(options =>
    {
        options.DefaultAuthenticateScheme =
            JwtBearerDefaults.AuthenticationScheme;

        options.DefaultChallengeScheme =
            JwtBearerDefaults.AuthenticationScheme;
    })
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = jwtSettings["Issuer"],

            ValidateAudience = true,
            ValidAudience = jwtSettings["Audience"],

            ValidateLifetime = true,

            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(key),

            ClockSkew = TimeSpan.FromSeconds(30)
        };
    });

builder.Services.AddAuthorization();
builder.Services.AddScoped<JwtTokenService>();
builder.Services.AddScoped<IProductRepository, ProductRepository>();
builder.Services.AddScoped<IProductSnapshotRepository, ProductSnapshotRepository>();
builder.Services.AddScoped<IProductVariantRepository, ProductVariantRepository>();
builder.Services.AddScoped<IProductPriceHistoryRepository, ProductPriceHistoryRepository>();
builder.Services.AddScoped<ProductService>();
builder.Services.AddScoped<IUnitOfWork, UnitOfWork>();
builder.Services.AddScoped<ProductMonitoringService>();
builder.Services.AddScoped<ProductResolutionService>();
builder.Services.AddScoped<IProductWatchRepository,ProductWatchRepository>();
builder.Services.AddScoped<WatchEvaluationService>();
builder.Services.AddScoped<NotificationService>();
builder.Services.AddScoped<INotificationRepository,NotificationRepository>();
builder.Services.AddScoped<ProductWatchService>();
builder.Services.AddHostedService<ProductMonitoringWorker>();

builder.Services.AddHttpClient<IProductScraperClient, ProductScraperClient>(
    client =>
    {
        client.BaseAddress = new Uri("http://localhost:8000/");
        client.Timeout = TimeSpan.FromSeconds(150);
    }
);


builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Name = "Authorization",
        Type = SecuritySchemeType.Http,
        Scheme = "bearer",
        BearerFormat = "JWT",
        In = ParameterLocation.Header,
        Description = "Enter your JWT token."
    });

    options.AddSecurityRequirement(document =>
        new OpenApiSecurityRequirement
        {
            [new OpenApiSecuritySchemeReference("Bearer", document)] = []
        });
});
var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();
app.Run();

