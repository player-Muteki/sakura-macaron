type Flavor = "sakura" | "pistachio" | "vanilla";

interface Macaron {
  readonly id: number;
  flavor: Flavor;
  price: number;
  available: boolean;
}

const collection: Macaron[] = [
  { id: 101, flavor: "sakura", price: 4.5, available: true },
  { id: 102, flavor: "pistachio", price: 4.2, available: true },
  { id: 103, flavor: "vanilla", price: 3.8, available: false },
];

export class SakuraCollection {
  constructor(private readonly items: Macaron[]) {}

  findByFlavor(flavor: Flavor): Macaron | undefined {
    return this.items.find(item => item.flavor === flavor);
  }

  get available(): Macaron[] {
    return this.items.filter(item => item.available);
  }

  formatPrice(item: Macaron): string {
    return `$${item.price.toFixed(2)}`;
  }
}

const shop = new SakuraCollection(collection);
const favorite = shop.findByFlavor("sakura");

if (favorite?.available) {
  console.log(`Sakura Macaron · ${shop.formatPrice(favorite)}`);
}

export const palette = {
  dark: "Soft blue · Warm rose · Sage green",
  light: "Cherry blossom · Muted teal · Deep berry",
  message: "A little color, a little clarity.",
};
