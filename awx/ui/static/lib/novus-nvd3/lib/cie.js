(function(d3) {
  var cie = d3.cie = {};

  cie.lab = function(l, a, b) {
    return arguments.length === 1
        ? (l instanceof Lab ? lab(l.l, l.a, l.b)
        : (l instanceof Lch ? lch_lab(l.l, l.c, l.h)
        : rgb_lab((l = d3.rgb(l)).r, l.g, l.b)))
        : lab(+l, +a, +b);
  };

  cie.lch = function(l, c, h) {
    return arguments.length === 1
        ? (l instanceof Lch ? lch(l.l, l.c, l.h)
        : (l instanceof Lab ? lab_lch(l.l, l.a, l.b)
        : lab_lch((l = rgb_lab((l = d3.rgb(l)).r, l.g, l.b)).l, l.a, l.b)))
        : lch(+l, +c, +h);
  };

  cie.interpolateLab = function(a, b) {
    a = cie.lab(a);
    b = cie.lab(b);
    var al = a.l,
        aa = a.a,
        ab = a.b,
        bl = b.l - al,
        ba = b.a - aa,
        bb = b.b - ab;
    return function(t) {
      return lab_rgb(al + bl * t, aa + ba * t, ab + bb * t) + "";
    };
  };

  cie.interpolateLch = function(a, b) {
    a = cie.lch(a);
    b = cie.lch(b);
    var al = a.l,
        ac = a.c,
        ah = a.h,
        bl = b.l - al,
        bc = b.c - ac,
        bh = b.h - ah;
    if (bh > 180) bh -= 360; else if (bh < -180) bh += 360; // shortest path
    return function(t) {
      return lch_lab(al + bl * t, ac + bc * t, ah + bh * t) + "";
    };
  };

  function lab(l, a, b) {
    return new Lab(l, a, b);
  }

  function Lab(l, a, b) {
    this.l = l;
    this.a = a;
    this.b = b;
  }

  Lab.prototype.brighter = function(k) {
    return lab(Math.min(100, this.l + K * (arguments.length ? k : 1)), this.a, this.b);
  };

  Lab.prototype.darker = function(k) {
    return lab(Math.max(0, this.l - K * (arguments.length ? k : 1)), this.a, this.b);
  };

  Lab.prototype.rgb = function() {
    return lab_rgb(this.l, this.a, this.b);
  };

  Lab.prototype.toString = function() {
    return this.rgb() + "";
  };

  function lch(l, c, h) {
    return new Lch(l, c, h);
  }

  function Lch(l, c, h) {
    this.l = l;
    this.c = c;
    this.h = h;
  }

  Lch.prototype.brighter = function(k) {
    return lch(Math.min(100, this.l + K * (arguments.length ? k : 1)), this.c, this.h);
  };

  Lch.prototype.darker = function(k) {
    return lch(Math.max(0, this.l - K * (arguments.length ? k : 1)), this.c, this.h);
  };

  Lch.prototype.rgb = function() {
    return lch_lab(this.l, this.c, this.h).rgb();
  };

  Lch.prototype.toString = function() {
    return this.rgb() + "";
  };

  // Corresponds roughly to RGB brighter/darker
  var K = 18;

  // D65 standard referent
  var X = 0.950470, Y = 1, Z = 1.088830;

  function lab_rgb(l, a, b) {
    var y = (l + 16) / 116, x = y + a / 500, z = y - b / 200;
    x = lab_xyz(x) * X;
    y = lab_xyz(y) * Y;
    z = lab_xyz(z) * Z;
    return d3.rgb(
      xyz_rgb( 3.2404542 * x - 1.5371385 * y - 0.4985314 * z),
      xyz_rgb(-0.9692660 * x + 1.8760108 * y + 0.0415560 * z),
      xyz_rgb( 0.0556434 * x - 0.2040259 * y + 1.0572252 * z)
    );
  }

  function rgb_lab(r, g, b) {
    r = rgb_xyz(r);
    g = rgb_xyz(g);
    b = rgb_xyz(b);
    var x = xyz_lab((0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / X),
        y = xyz_lab((0.2126729 * r + 0.7151522 * g + 0.0721750 * b) / Y),
        z = xyz_lab((0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / Z);
    return lab(116 * y - 16, 500 * (x - y), 200 * (y - z));
  }

  function lab_lch(l, a, b) {
    var c = Math.sqrt(a * a + b * b),
        h = Math.atan2(b, a) / Math.PI * 180;
    return lch(l, c, h);
  }

  function lch_lab(l, c, h) {
    h = h * Math.PI / 180;
    return lab(l, Math.cos(h) * c, Math.sin(h) * c);
  }

  function lab_xyz(x) {
    return x > 0.206893034 ? x * x * x : (x - 4 / 29) / 7.787037;
  }

  function xyz_lab(x) {
    return x > 0.008856 ? Math.pow(x, 1 / 3) : 7.787037 * x + 4 / 29;
  }

  function xyz_rgb(r) {
    return Math.round(255 * (r <= 0.00304 ? 12.92 * r : 1.055 * Math.pow(r, 1 / 2.4) - 0.055));
  }

  function rgb_xyz(r) {
    return (r /= 255) <= 0.04045 ? r / 12.92 : Math.pow((r + 0.055) / 1.055, 2.4);
  }
})(d3);
