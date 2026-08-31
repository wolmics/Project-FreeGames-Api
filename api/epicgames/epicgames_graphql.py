GRAPHQL_URL = "https://store.epicgames.com/graphql"

SCAN_QUERY = """
query searchStoreQuery(
  $allowCountries: String
  $category: String
  $count: Int
  $country: String!
  $locale: String
  $sortBy: String
  $sortDir: String
  $start: Int
  $freeGame: Boolean
) {
  Catalog {
    searchStore(
      allowCountries: $allowCountries
      category: $category
      count: $count
      country: $country
      locale: $locale
      sortBy: $sortBy
      sortDir: $sortDir
      start: $start
      freeGame: $freeGame
    ) {
      elements {
        id
        namespace
        title
        price(country: $country) {
          totalPrice {
            discountPrice
            originalPrice
          }
        }
        promotions {
          promotionalOffers {
            promotionalOffers {
              startDate
            }
          }
        }
      }
      paging {
        count
        total
      }
    }
  }
}
"""

DETAILS_QUERY = """
query getCatalogOfferDetails(
  $sandboxId: String!
  $offerId: String!
  $locale: String
  $country: String!
) {
  Catalog {
    catalogOffer(namespace: $sandboxId, id: $offerId, locale: $locale) {
      title
      description
      productSlug
      keyImages {
        type
        url
      }
      price(country: $country) {
        totalPrice {
          fmtPrice(locale: $locale) {
            originalPrice
            discountPrice
          }
        }
      }
      promotions {
        promotionalOffers {
          promotionalOffers {
            startDate
            endDate
          }
        }
      }
      offerMappings {
        pageSlug
      }
    }
  }
}
"""