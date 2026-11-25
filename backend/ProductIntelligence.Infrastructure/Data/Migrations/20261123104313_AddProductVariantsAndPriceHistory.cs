using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ProductIntelligence.Infrastructure.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddProductVariantsAndPriceHistory : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_ProductWatches_Products_ProductId",
                table: "ProductWatches");

            migrationBuilder.DropColumn(
                name: "SelectedColor",
                table: "ProductWatches");

            migrationBuilder.DropColumn(
                name: "SelectedSize",
                table: "ProductWatches");

            migrationBuilder.RenameColumn(
                name: "ProductId",
                table: "ProductWatches",
                newName: "ProductVariantId");

            migrationBuilder.RenameIndex(
                name: "IX_ProductWatches_ProductId_IsActive",
                table: "ProductWatches",
                newName: "IX_ProductWatches_ProductVariantId_IsActive");

            migrationBuilder.AddColumn<bool>(
                name: "AvailabilityConditionMet",
                table: "ProductWatches",
                type: "bit",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<DateTime>(
                name: "LastNotifiedAtUtc",
                table: "ProductWatches",
                type: "datetime2",
                nullable: true);

            migrationBuilder.AddColumn<bool>(
                name: "PriceConditionMet",
                table: "ProductWatches",
                type: "bit",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AlterColumn<string>(
                name: "Title",
                table: "Products",
                type: "nvarchar(500)",
                maxLength: 500,
                nullable: false,
                oldClrType: typeof(string),
                oldType: "nvarchar(max)");

            migrationBuilder.AlterColumn<string>(
                name: "ProductUrl",
                table: "Products",
                type: "nvarchar(2048)",
                maxLength: 2048,
                nullable: false,
                oldClrType: typeof(string),
                oldType: "nvarchar(max)");

            migrationBuilder.AlterColumn<string>(
                name: "Platform",
                table: "Products",
                type: "nvarchar(50)",
                maxLength: 50,
                nullable: false,
                oldClrType: typeof(string),
                oldType: "nvarchar(max)");

            migrationBuilder.AlterColumn<string>(
                name: "ExternalProductId",
                table: "Products",
                type: "nvarchar(100)",
                maxLength: 100,
                nullable: true,
                oldClrType: typeof(string),
                oldType: "nvarchar(max)",
                oldNullable: true);

            migrationBuilder.CreateTable(
                name: "ProductVariants",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uniqueidentifier", nullable: false),
                    ProductId = table.Column<Guid>(type: "uniqueidentifier", nullable: false),
                    Color = table.Column<string>(type: "nvarchar(100)", maxLength: 100, nullable: false),
                    Size = table.Column<string>(type: "nvarchar(50)", maxLength: 50, nullable: false),
                    CurrentPrice = table.Column<decimal>(type: "decimal(18,2)", precision: 18, scale: 2, nullable: true),
                    MinPrice = table.Column<decimal>(type: "decimal(18,2)", precision: 18, scale: 2, nullable: true),
                    MaxPrice = table.Column<decimal>(type: "decimal(18,2)", precision: 18, scale: 2, nullable: true),
                    IsAvailable = table.Column<bool>(type: "bit", nullable: false),
                    LastUpdatedAtUtc = table.Column<DateTime>(type: "datetime2", nullable: false),
                    LastChangedAtUtc = table.Column<DateTime>(type: "datetime2", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ProductVariants", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ProductVariants_Products_ProductId",
                        column: x => x.ProductId,
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ProductPriceHistory",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uniqueidentifier", nullable: false),
                    ProductVariantId = table.Column<Guid>(type: "uniqueidentifier", nullable: false),
                    Price = table.Column<decimal>(type: "decimal(18,2)", precision: 18, scale: 2, nullable: true),
                    IsAvailable = table.Column<bool>(type: "bit", nullable: false),
                    ObservedAtUtc = table.Column<DateTime>(type: "datetime2", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ProductPriceHistory", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ProductPriceHistory_ProductVariants_ProductVariantId",
                        column: x => x.ProductVariantId,
                        principalTable: "ProductVariants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_ProductWatches_UserId_IsActive",
                table: "ProductWatches",
                columns: new[] { "UserId", "IsActive" });

            migrationBuilder.CreateIndex(
                name: "IX_Products_ProductUrl",
                table: "Products",
                column: "ProductUrl",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ProductPriceHistory_ProductVariantId_ObservedAtUtc",
                table: "ProductPriceHistory",
                columns: new[] { "ProductVariantId", "ObservedAtUtc" });

            migrationBuilder.CreateIndex(
                name: "IX_ProductVariants_ProductId_Color_Size",
                table: "ProductVariants",
                columns: new[] { "ProductId", "Color", "Size" },
                unique: true);

            migrationBuilder.AddForeignKey(
                name: "FK_ProductWatches_ProductVariants_ProductVariantId",
                table: "ProductWatches",
                column: "ProductVariantId",
                principalTable: "ProductVariants",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_ProductWatches_ProductVariants_ProductVariantId",
                table: "ProductWatches");

            migrationBuilder.DropTable(
                name: "ProductPriceHistory");

            migrationBuilder.DropTable(
                name: "ProductVariants");

            migrationBuilder.DropIndex(
                name: "IX_ProductWatches_UserId_IsActive",
                table: "ProductWatches");

            migrationBuilder.DropIndex(
                name: "IX_Products_ProductUrl",
                table: "Products");

            migrationBuilder.DropColumn(
                name: "AvailabilityConditionMet",
                table: "ProductWatches");

            migrationBuilder.DropColumn(
                name: "LastNotifiedAtUtc",
                table: "ProductWatches");

            migrationBuilder.DropColumn(
                name: "PriceConditionMet",
                table: "ProductWatches");

            migrationBuilder.RenameColumn(
                name: "ProductVariantId",
                table: "ProductWatches",
                newName: "ProductId");

            migrationBuilder.RenameIndex(
                name: "IX_ProductWatches_ProductVariantId_IsActive",
                table: "ProductWatches",
                newName: "IX_ProductWatches_ProductId_IsActive");

            migrationBuilder.AddColumn<string>(
                name: "SelectedColor",
                table: "ProductWatches",
                type: "nvarchar(100)",
                maxLength: 100,
                nullable: false,
                defaultValue: "");

            migrationBuilder.AddColumn<string>(
                name: "SelectedSize",
                table: "ProductWatches",
                type: "nvarchar(50)",
                maxLength: 50,
                nullable: false,
                defaultValue: "");

            migrationBuilder.AlterColumn<string>(
                name: "Title",
                table: "Products",
                type: "nvarchar(max)",
                nullable: false,
                oldClrType: typeof(string),
                oldType: "nvarchar(500)",
                oldMaxLength: 500);

            migrationBuilder.AlterColumn<string>(
                name: "ProductUrl",
                table: "Products",
                type: "nvarchar(max)",
                nullable: false,
                oldClrType: typeof(string),
                oldType: "nvarchar(2048)",
                oldMaxLength: 2048);

            migrationBuilder.AlterColumn<string>(
                name: "Platform",
                table: "Products",
                type: "nvarchar(max)",
                nullable: false,
                oldClrType: typeof(string),
                oldType: "nvarchar(50)",
                oldMaxLength: 50);

            migrationBuilder.AlterColumn<string>(
                name: "ExternalProductId",
                table: "Products",
                type: "nvarchar(max)",
                nullable: true,
                oldClrType: typeof(string),
                oldType: "nvarchar(100)",
                oldMaxLength: 100,
                oldNullable: true);

            migrationBuilder.AddForeignKey(
                name: "FK_ProductWatches_Products_ProductId",
                table: "ProductWatches",
                column: "ProductId",
                principalTable: "Products",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);
        }
    }
}
