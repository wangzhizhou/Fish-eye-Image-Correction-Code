// Improved fisheye correction (research proposal, NOT the original program/ code).
// Only the modern cv:: C++ API is used, so it builds against OpenCV 4.x and 5.x.
//
// Conventions (identical to program/corrector.cpp so results are comparable):
//   colatitude phi in [0, pi] measured from +y (up), longitude lam in [0, pi],
//   x = -sin(phi) cos(lam), y = cos(phi), z = sin(phi) sin(lam), z = optical axis.
//   Geographic latitude psi = pi/2 - phi, longitude offset lam' = lam - pi/2.
//   Fisheye image: x_c = u - cx, y_c = -(v - cy), alpha = atan2(y_c, x_c).
#pragma once
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <string>
#include <vector>

namespace fisheye {

enum class Lens { Stereographic, Equidistant, Equisolid, Orthographic };
Lens parseLens(const std::string& s);

struct Circle { double cx = 0, cy = 0, r = 0; };          // double: no int truncation (BUG-08)

struct Camera {
    Circle circle;
    Lens lens = Lens::Equidistant;
    double fov = CV_PI;                                     // full field of view, radians
    double focal() const;                                   // p(fov/2) = r
    double thetaToP(double theta) const;                    // lens model, forward
    double pToTheta(double p) const;                        // lens model, inverse (same model! BUG-04)
    double thetaMax() const { return fov / 2; }
};

// One axis of a separable "cylindrical" output map: angle a (lat psi or lon lam') <-> coordinate s.
//   Linear: s = a                (equirectangular / paper Eq.17 longitude)
//   LCCP:   s = sgn(a) 2 sin w sin(|a|/2) / sin(w + |a|/2)   (closed form of auxFunc, w in (0, 3pi/4))
//           w = pi/2 gives Braun 2 tan(a/2) (= getPhi of Correction3).
struct AxisMap {
    enum Kind { Linear, LCCP } kind = Linear;
    double w = CV_PI / 2;
    double forward(double a) const;                         // a -> s
    double inverse(double s) const;                         // s -> a (closed form, no bisection: BUG-01/02/03)
    double slopeAt0() const { return 1.0; }                 // ds/da at a = 0 is 1 for both kinds
};

struct OutputSpec {
    AxisMap lon, lat;
    double lonHalf = CV_PI / 2;   // covered half-range of lam' and psi (clipped to fov/2 when clipToFov)
    double latHalf = CV_PI / 2;
    bool clipToFov = true;        // BUG-13/14: range follows the lens fov
    int width = 0, height = 0;    // 0 => derived from the circle radius (BUG-17)
};

// Resolve ranges and size. Size rule: 1 output pixel per fisheye pixel at the image centre,
// i.e. W = f * (s(lonHalf) - s(-lonHalf)) * scale.
OutputSpec resolve(const Camera& cam, OutputSpec spec, double scale = 1.0);

// Pixel-centre convention: column i covers s in [s0 + i ds, s0 + (i+1) ds], sampled at its centre.
double colToLon(const OutputSpec& o, double i);              // returns lam (in [0, pi])
double rowToLat(const OutputSpec& o, double j);              // returns psi (north up)
double lonToCol(const OutputSpec& o, double lam);
double latToRow(const OutputSpec& o, double psi);

// Inverse maps for cv::remap (CV_32FC1). Pixels whose ray is outside the lens fov get -1.
void buildMaps(const Camera& cam, const OutputSpec& o, cv::Mat& mapx, cv::Mat& mapy);
// Corrected image: bilinear remap, black outside the fisheye circle (BUG-06/19).
cv::Mat correct(const cv::Mat& img, const Camera& cam, const OutputSpec& o);

// Point transforms (continuous, exact; use cvRound if integers are needed: BUG-05).
bool fisheyeToOutput(const Camera& cam, const OutputSpec& o, double u, double v, double& col, double& row);
bool outputToFisheye(const Camera& cam, const OutputSpec& o, double col, double row, double& u, double& v);

// Panorama viewer with the SAME geometry as program/viewer.cpp (poles on +-z, lon = atan2(y,x),
// rotation V*H, eye distance d), but rays precomputed once and bilinear remap with horizontal wrap.
class Viewer {
public:
    Viewer(const cv::Mat& pano, int width = 1024, int height = 512, double distance = 300);
    cv::Mat render(double angleH, double angleV);
private:
    cv::Mat pano_;      // panorama with one wrapped column appended
    int W_, H_;
    cv::Mat rays_;      // CV_64FC3, unit rays of the window (depends only on size and distance)
};

}  // namespace fisheye
