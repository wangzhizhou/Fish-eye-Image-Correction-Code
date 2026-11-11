#include "fisheye_improved.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace fisheye {

Lens parseLens(const std::string& s)
{
    if (s == "STEREOGRAPHIC") return Lens::Stereographic;
    if (s == "EQUIDISTANCE" || s == "EQUIDISTANT") return Lens::Equidistant;
    if (s == "EQUISOLID") return Lens::Equisolid;
    if (s == "ORTHOGONAL" || s == "ORTHOGRAPHIC") return Lens::Orthographic;
    throw std::invalid_argument("unknown lens model: " + s);
}

// ---------------------------------------------------------------- lens models
double Camera::focal() const
{
    if (!(fov > 0) || circle.r <= 0) throw std::invalid_argument("fov and radius must be > 0");
    switch (lens) {
    case Lens::Stereographic: return circle.r / (2 * std::tan(fov / 4));
    case Lens::Equidistant:   return circle.r / (fov / 2);
    case Lens::Equisolid:     return circle.r / (2 * std::sin(fov / 4));
    case Lens::Orthographic:
        if (fov > CV_PI) throw std::invalid_argument("orthographic lens: fov must be <= pi");
        return circle.r / std::sin(fov / 2);
    }
    return 0;
}

double Camera::thetaToP(double t) const
{
    const double f = focal();
    switch (lens) {
    case Lens::Stereographic: return 2 * f * std::tan(t / 2);
    case Lens::Equidistant:   return f * t;
    case Lens::Equisolid:     return 2 * f * std::sin(t / 2);
    case Lens::Orthographic:  return f * std::sin(t);
    }
    return 0;
}

double Camera::pToTheta(double p) const
{
    const double f = focal();
    switch (lens) {
    case Lens::Stereographic: return 2 * std::atan(p / (2 * f));
    case Lens::Equidistant:   return p / f;
    case Lens::Equisolid:     return 2 * std::asin(std::min(1.0, p / (2 * f)));
    case Lens::Orthographic:  return std::asin(std::min(1.0, p / f));
    }
    return 0;
}

// ---------------------------------------------------------------- axis maps
double AxisMap::forward(double a) const
{
    if (kind == Linear) return a;
    if (!(w > 0 && w < 3 * CV_PI / 4)) throw std::invalid_argument("LCCP w must lie in (0, 3pi/4)");
    const double h = std::fabs(a) / 2;
    const double s = 2 * std::sin(w) * std::sin(h) / std::sin(w + h);
    return a < 0 ? -s : s;
}

double AxisMap::inverse(double s) const
{
    if (kind == Linear) return s;
    const double as = std::fabs(s);
    // 2 sin w sin a / sin(w + a) = s  <=>  a = atan2(s sin w, 2 sin w - s cos w)   (SymPy-verified)
    const double h = std::atan2(as * std::sin(w), 2 * std::sin(w) - as * std::cos(w));
    return s < 0 ? -2 * h : 2 * h;
}

OutputSpec resolve(const Camera& cam, OutputSpec o, double scale)
{
    if (o.clipToFov) {
        o.lonHalf = std::min(o.lonHalf, cam.thetaMax());
        o.latHalf = std::min(o.latHalf, cam.thetaMax());
    }
    const double f = cam.focal();
    // the lens is ~f px/rad at the centre for all four models; the axis maps have unit slope at 0
    if (o.width <= 0)
        o.width = std::max(16, (int)std::lround(scale * f * (o.lon.forward(o.lonHalf) - o.lon.forward(-o.lonHalf))));
    if (o.height <= 0)
        o.height = std::max(16, (int)std::lround(scale * f * (o.lat.forward(o.latHalf) - o.lat.forward(-o.latHalf))));
    return o;
}

double colToLon(const OutputSpec& o, double i)
{
    const double s0 = o.lon.forward(-o.lonHalf), s1 = o.lon.forward(o.lonHalf);
    return CV_PI / 2 + o.lon.inverse(s0 + (i + 0.5) * (s1 - s0) / o.width);
}
double rowToLat(const OutputSpec& o, double j)
{
    const double s0 = o.lat.forward(o.latHalf), s1 = o.lat.forward(-o.latHalf);   // row 0 = north
    return o.lat.inverse(s0 + (j + 0.5) * (s1 - s0) / o.height);
}
double lonToCol(const OutputSpec& o, double lam)
{
    const double s0 = o.lon.forward(-o.lonHalf), s1 = o.lon.forward(o.lonHalf);
    return (o.lon.forward(lam - CV_PI / 2) - s0) / (s1 - s0) * o.width - 0.5;
}
double latToRow(const OutputSpec& o, double psi)
{
    const double s0 = o.lat.forward(o.latHalf), s1 = o.lat.forward(-o.latHalf);
    return (o.lat.forward(psi) - s0) / (s1 - s0) * o.height - 0.5;
}

// ---------------------------------------------------------------- point transforms
static bool latlonToFisheye(const Camera& cam, double psi, double lam, double& u, double& v)
{
    const double phi = CV_PI / 2 - psi;
    const double x = -std::sin(phi) * std::cos(lam), y = std::cos(phi), z = std::sin(phi) * std::sin(lam);
    const double theta = std::acos(std::max(-1.0, std::min(1.0, z)));
    if (theta > cam.thetaMax() + 1e-12) return false;
    const double alpha = std::atan2(y, x);                  // exact atan2, not cvFastArctan (BUG-20)
    const double p = cam.thetaToP(theta);
    u = cam.circle.cx + p * std::cos(alpha);
    v = cam.circle.cy - p * std::sin(alpha);
    return true;
}

bool outputToFisheye(const Camera& cam, const OutputSpec& o, double col, double row, double& u, double& v)
{
    return latlonToFisheye(cam, rowToLat(o, row), colToLon(o, col), u, v);
}

bool fisheyeToOutput(const Camera& cam, const OutputSpec& o, double u, double v, double& col, double& row)
{
    const double xc = u - cam.circle.cx, yc = -(v - cam.circle.cy);
    const double p = std::hypot(xc, yc);
    if (p > cam.circle.r) return false;
    const double theta = cam.pToTheta(p), alpha = std::atan2(yc, xc);
    const double x = std::sin(theta) * std::cos(alpha), y = std::sin(theta) * std::sin(alpha), z = std::cos(theta);
    const double phi = std::acos(std::max(-1.0, std::min(1.0, y)));
    const double lam = std::atan2(z, -x);                   // in [0, pi] because z >= 0 on the hemisphere
    col = lonToCol(o, lam);
    row = latToRow(o, CV_PI / 2 - phi);
    return true;
}

// ---------------------------------------------------------------- maps & correction
void buildMaps(const Camera& cam, const OutputSpec& o, cv::Mat& mapx, cv::Mat& mapy)
{
    if (o.width <= 0 || o.height <= 0) throw std::invalid_argument("call resolve() first");
    // separable: latitude depends only on the row, longitude only on the column (BUG-21)
    std::vector<double> sl(o.height), cl(o.height), sm(o.width), cm(o.width);
    for (int j = 0; j < o.height; j++) { const double ph = CV_PI / 2 - rowToLat(o, j); sl[j] = std::sin(ph); cl[j] = std::cos(ph); }
    for (int i = 0; i < o.width; i++) { const double lm = colToLon(o, i); sm[i] = std::sin(lm); cm[i] = std::cos(lm); }
    const double tmax = cam.thetaMax(), cx = cam.circle.cx, cy = cam.circle.cy;
    mapx.create(o.height, o.width, CV_32F);
    mapy.create(o.height, o.width, CV_32F);
    cv::parallel_for_(cv::Range(0, o.height), [&](const cv::Range& r) {
        for (int j = r.start; j < r.end; j++) {
            float* mx = mapx.ptr<float>(j);
            float* my = mapy.ptr<float>(j);
            for (int i = 0; i < o.width; i++) {
                const double x = -sl[j] * cm[i], y = cl[j], z = sl[j] * sm[i];
                const double theta = std::acos(std::max(-1.0, std::min(1.0, z)));
                if (theta > tmax + 1e-12) { mx[i] = my[i] = -1.f; continue; }   // outside the lens fov
                const double rho = std::hypot(x, y);
                const double p = cam.thetaToP(theta);
                const double ca = rho > 0 ? x / rho : 1.0, sa = rho > 0 ? y / rho : 0.0;
                mx[i] = (float)(cx + p * ca);
                my[i] = (float)(cy - p * sa);
            }
        }
    });
}

cv::Mat correct(const cv::Mat& img, const Camera& cam, const OutputSpec& o)
{
    cv::Mat mx, my, out;
    buildMaps(cam, o, mx, my);
    // remap never reads outside the image (BUG-06): BORDER_CONSTANT returns black there
    cv::remap(img, out, mx, my, cv::INTER_LINEAR, cv::BORDER_CONSTANT, cv::Scalar::all(0));
    // keep the inside of the fisheye circle only (pixels beyond r carry no scene content)
    cv::Mat outside = (mx < 0) | (my < 0);
    cv::Mat dx = mx - (float)cam.circle.cx, dy = my - (float)cam.circle.cy, rr;
    cv::magnitude(dx, dy, rr);
    outside |= rr > (float)(cam.circle.r + 0.5);
    out.setTo(cv::Scalar::all(0), outside);
    return out;
}

// ---------------------------------------------------------------- viewer
Viewer::Viewer(const cv::Mat& pano, int width, int height, double distance)
{
    W_ = pano.cols; H_ = pano.rows;
    cv::hconcat(pano, pano.col(0), pano_);                  // horizontal wrap for bilinear sampling
    rays_.create(height, width, CV_64FC3);
    const int cx = width / 2, cy = height / 2;
    for (int j = 0; j < height; j++)
        for (int i = 0; i < width; i++) {
            cv::Vec3d p(i - cx, cy - j, distance);
            rays_.at<cv::Vec3d>(j, i) = p / cv::norm(p);
        }
}

cv::Mat Viewer::render(double aH, double aV)
{
    const cv::Matx33d MH(std::cos(aH), 0, -std::sin(aH), 0, 1, 0, std::sin(aH), 0, std::cos(aH));
    const cv::Matx33d MV(1, 0, 0, 0, std::cos(aV), -std::sin(aV), 0, std::sin(aV), std::cos(aV));
    cv::Mat rot;
    cv::transform(rays_, rot, cv::Mat(MV * MH));             // one 3x3 product for the whole window
    cv::Mat mx(rays_.size(), CV_32F), my(rays_.size(), CV_32F);
    cv::parallel_for_(cv::Range(0, rays_.rows), [&](const cv::Range& r) {
        for (int j = r.start; j < r.end; j++) {
            const cv::Vec3d* q = rot.ptr<cv::Vec3d>(j);
            float* px = mx.ptr<float>(j);
            float* py = my.ptr<float>(j);
            for (int i = 0; i < rays_.cols; i++) {
                double lon = std::atan2(q[i][1], q[i][0]);
                if (lon < 0) lon += 2 * CV_PI;
                const double lat = std::acos(std::max(-1.0, std::min(1.0, q[i][2])));
                // pixel-centre convention: column u covers lon in [u, u+1) * 2pi/W
                px[i] = (float)(lon / (2 * CV_PI) * W_ - 0.5);
                py[i] = (float)(lat / CV_PI * H_ - 0.5);
            }
        }
    });
    cv::Mat out;
    cv::remap(pano_, out, mx, my, cv::INTER_LINEAR, cv::BORDER_REPLICATE);
    return out;
}

}  // namespace fisheye
