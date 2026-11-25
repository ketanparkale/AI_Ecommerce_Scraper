using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ProductIntelligence.Infrastructure.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddExternalVariantIds : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "ColorExternalId",
                table: "ProductVariants",
                type: "nvarchar(150)",
                maxLength: 150,
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "SizeExternalId",
                table: "ProductVariants",
                type: "nvarchar(150)",
                maxLength: 150,
                nullable: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "ColorExternalId",
                table: "ProductVariants");

            migrationBuilder.DropColumn(
                name: "SizeExternalId",
                table: "ProductVariants");
        }
    }
}
