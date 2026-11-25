
using Microsoft.EntityFrameworkCore;
using ProductIntelligence.Core.Products.Entities;
using ProductIntelligence.Core.Notifications.Entities;
using ProductIntelligence.Core.Watches.Entities;
using ProductIntelligence.Infrastructure.Repositories;

namespace ProductIntelligence.Infrastructure.Data;

public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(
        DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    public DbSet<Product> Products => Set<Product>();

    public DbSet<ProductSnapshot> ProductSnapshots => Set<ProductSnapshot>();

    public DbSet<ProductWatch> ProductWatches => Set<ProductWatch>();

    public DbSet<Notification> Notifications => Set<Notification>();

    public DbSet<ProductVariantSnapshot> ProductVariantSnapshots
    => Set<ProductVariantSnapshot>();

    public DbSet<ProductVariant> ProductVariants
    => Set<ProductVariant>();

    public DbSet<ProductPriceHistory> ProductPriceHistories
    => Set<ProductPriceHistory>();

    
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Product configuration
        modelBuilder.Entity<Product>(entity =>
        {
            entity.ToTable("Products");

            entity.HasKey(p => p.Id);

            entity.Property(p => p.ProductUrl)
                .IsRequired()
                .HasMaxLength(2048);

            entity.Property(p => p.Platform)
                .IsRequired()
                .HasMaxLength(50);

            entity.Property(p => p.ExternalProductId)
                .HasMaxLength(100);

            entity.Property(p => p.Title)
                .IsRequired()
                .HasMaxLength(500);

            entity.HasIndex(p => p.ProductUrl)
                .IsUnique();
        });

        // ProductVariant configuration
        modelBuilder.Entity<ProductVariant>(entity =>
        {
            entity.ToTable("ProductVariants");

            entity.HasKey(v => v.Id);

            entity.Property(v => v.Color)
                .IsRequired()
                .HasMaxLength(100);

            entity.Property(v => v.Size)
                .IsRequired()
                .HasMaxLength(50);

            entity.Property(v => v.CurrentPrice)
                .HasPrecision(18, 2);

            entity.Property(v => v.MinPrice)
                .HasPrecision(18, 2);

            entity.Property(v => v.MaxPrice)
                .HasPrecision(18, 2);

            entity.HasOne<Product>()
                .WithMany()
                .HasForeignKey(v => v.ProductId)
                .OnDelete(DeleteBehavior.Cascade);

            entity.Property(v => v.ColorExternalId)
                .HasMaxLength(150);

            entity.Property(v => v.SizeExternalId)
                .HasMaxLength(150);

            // One unique color/size combination per product
            entity.HasIndex(v => new
            {
                v.ProductId,
                v.Color,
                v.Size
            }).IsUnique();
        });

        // ProductPriceHistory configuration
        modelBuilder.Entity<ProductPriceHistory>(entity =>
        {
            entity.ToTable("ProductPriceHistory");

            entity.HasKey(h => h.Id);

            entity.Property(h => h.Price)
                .HasPrecision(18, 2);

            entity.HasOne(h => h.ProductVariant)
                .WithMany()
                .HasForeignKey(h => h.ProductVariantId)
                .OnDelete(DeleteBehavior.Cascade);

            entity.HasIndex(h => new
            {
                h.ProductVariantId,
                h.ObservedAtUtc
            });
        });

        // ProductWatch configuration
        modelBuilder.Entity<ProductWatch>(entity =>
        {
            entity.ToTable("ProductWatches");

            entity.HasKey(w => w.Id);

            entity.Property(w => w.TargetPrice)
                .HasPrecision(18, 2);

            entity.HasOne(w => w.ProductVariant)
                .WithMany()
                .HasForeignKey(w => w.ProductVariantId)
                .OnDelete(DeleteBehavior.Cascade);

            entity.HasIndex(w => new
            {
                w.ProductVariantId,
                w.IsActive
            });

            entity.HasIndex(w => new
            {
                w.UserId,
                w.IsActive
            });
        });

        // Notification configuration
        modelBuilder.Entity<Notification>(entity =>
        {
            entity.ToTable("Notifications");

            entity.HasKey(n => n.Id);

            entity.Property(n => n.Type)
                .IsRequired();

            entity.Property(n => n.Title)
                .IsRequired()
                .HasMaxLength(200);

            entity.Property(n => n.Message)
                .IsRequired()
                .HasMaxLength(1000);

            entity.HasOne<ProductWatch>()
                .WithMany()
                .HasForeignKey(n => n.ProductWatchId)
                .OnDelete(DeleteBehavior.Cascade);

            entity.HasIndex(n => new
            {
                n.UserId,
                n.IsRead,
                n.CreatedAtUtc
            });
        });

        // Keep existing snapshot configuration temporarily.
        modelBuilder.Entity<ProductSnapshot>(entity =>
        {
            entity.ToTable("ProductSnapshots");

            entity.HasKey(s => s.Id);

            entity.HasOne<Product>()
                .WithMany()
                .HasForeignKey(s => s.ProductId)
                .OnDelete(DeleteBehavior.Cascade);

            entity.HasMany(s => s.Variants)
                .WithOne(v => v.ProductSnapshot)
                .HasForeignKey(v => v.ProductSnapshotId)
                .OnDelete(DeleteBehavior.Cascade);

            entity.HasIndex(s => new
            {
                s.ProductId,
                s.CapturedAtUtc
            });
        });

        modelBuilder.Entity<ProductVariantSnapshot>(entity =>
        {
            entity.ToTable("ProductVariantSnapshots");

            entity.HasKey(v => v.Id);

            entity.Property(v => v.Color)
                .IsRequired()
                .HasMaxLength(100);

            entity.Property(v => v.Size)
                .IsRequired()
                .HasMaxLength(50);

            entity.Property(v => v.Price)
                .HasPrecision(18, 2);
        });
    }

}
