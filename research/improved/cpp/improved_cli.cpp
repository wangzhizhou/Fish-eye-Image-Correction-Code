// Command-line driver for the improved implementation (non-interactive; no GUI).
//   improved_cli correct   in=IMG out=PNG cx= cy= r= [lens=EQUIDISTANCE fov=pi lon=lin lat=lccp:1.5708 w=0 h=0 scale=1 clip=1]
//   improved_cli maps      out=BIN  (same camera/output keys)   -> int32 H, int32 W, float32 mapx[H*W], mapy[H*W]
//   improved_cli roundtrip out=TXT  (same keys) [step=4]          -> integer and continuous round-trip errors
//   improved_cli viewer    in=PANO out=PNG [aH=0 aV=1.5708 reps=1]
//   improved_cli time      in=IMG reps=N (same keys)              -> ms per correct() call
//   improved_cli statics   (no keys)                              -> checks that changing w in one process is safe
//   improved_cli imgdiff   a=IMG b=IMG [max_mae=1]                -> mean abs difference; exit 3 if > max_mae (CI)
//   roundtrip check=1      exit 3 unless cont_max < 1e-9 and |bias| < 0.01 px (CI)
// Axis spec: "lin" or "lccp:<w>".  fov accepts "pi" or a number in radians.
#include "fisheye_improved.hpp"
#include <opencv2/imgcodecs.hpp>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <iterator>
#include <map>
#include <string>
#include <vector>

using namespace fisheye;

static std::map<std::string, std::string> kv(int argc, char** argv)
{
    std::map<std::string, std::string> m;
    for (int k = 2; k < argc; k++) {
        std::string a = argv[k];
        const size_t e = a.find('=');
        if (e == std::string::npos) throw std::invalid_argument("expected key=value, got " + a);
        m[a.substr(0, e)] = a.substr(e + 1);
    }
    return m;
}
static std::string get(const std::map<std::string, std::string>& m, const std::string& k, const std::string& d)
{
    auto it = m.find(k);
    return it == m.end() ? d : it->second;
}
static double num(const std::string& s) { return s == "pi" ? CV_PI : std::stod(s); }
static AxisMap axis(const std::string& s)
{
    AxisMap a;
    if (s == "lin") { a.kind = AxisMap::Linear; return a; }
    if (s.rfind("lccp:", 0) == 0) { a.kind = AxisMap::LCCP; a.w = num(s.substr(5)); return a; }
    throw std::invalid_argument("axis must be lin or lccp:<w>: " + s);
}
static void setup(const std::map<std::string, std::string>& m, Camera& cam, OutputSpec& o)
{
    cam.circle.cx = num(get(m, "cx", "0"));
    cam.circle.cy = num(get(m, "cy", "0"));
    cam.circle.r = num(get(m, "r", "0"));
    cam.lens = parseLens(get(m, "lens", "EQUIDISTANCE"));
    cam.fov = num(get(m, "fov", "pi"));
    o.lon = axis(get(m, "lon", "lin"));
    o.lat = axis(get(m, "lat", "lccp:1.5707963267948966"));
    o.width = std::stoi(get(m, "w", "0"));
    o.height = std::stoi(get(m, "h", "0"));
    o.clipToFov = get(m, "clip", "1") == "1";
    o = resolve(cam, o, num(get(m, "scale", "1")));
}

int main(int argc, char** argv)
{
    if (argc < 2) { std::fprintf(stderr, "see header of improved_cli.cpp\n"); return 2; }
    const std::string cmd = argv[1];
    try {
        auto m = kv(argc, argv);
        if (m.count("threads")) cv::setNumThreads(std::stoi(m["threads"]));
        Camera cam;
        OutputSpec o;
        if (cmd == "correct" || cmd == "maps" || cmd == "roundtrip" || cmd == "time") setup(m, cam, o);

        if (cmd == "correct") {
            cv::Mat img = cv::imread(get(m, "in", ""), cv::IMREAD_COLOR);
            if (img.empty()) throw std::runtime_error("cannot read input");
            cv::Mat out = correct(img, cam, o);
            if (!cv::imwrite(get(m, "out", "out.png"), out)) throw std::runtime_error("cannot write output");
            std::printf("output %d x %d\n", o.width, o.height);
            return 0;
        }
        if (cmd == "maps") {
            cv::Mat mx, my;
            buildMaps(cam, o, mx, my);
            std::ofstream f(get(m, "out", "maps.bin"), std::ios::binary);
            int32_t hw[2] = {o.height, o.width};
            f.write((const char*)hw, sizeof hw);
            f.write((const char*)mx.data, mx.total() * sizeof(float));
            f.write((const char*)my.data, my.total() * sizeof(float));
            return 0;
        }
        if (cmd == "roundtrip") {
            const int step = std::stoi(get(m, "step", "4"));
            double cs = 0, cmax = 0, is = 0, imax = 0, bu = 0, bv = 0;
            long n = 0;
            const Circle& c = cam.circle;
            for (int v = (int)std::ceil(c.cy - c.r); v <= (int)std::floor(c.cy + c.r); v += step)
                for (int u = (int)std::ceil(c.cx - c.r); u <= (int)std::floor(c.cx + c.r); u += step) {
                    double col, row, u2, v2;
                    if (!fisheyeToOutput(cam, o, u, v, col, row)) continue;
                    if (col < -0.5 || row < -0.5 || col > o.width - 0.5 || row > o.height - 0.5) continue;
                    // continuous
                    if (!outputToFisheye(cam, o, col, row, u2, v2)) continue;
                    const double ec = std::hypot(u2 - u, v2 - v);
                    // integer pipeline: round the output pixel, map back, round the fisheye pixel (BUG-05)
                    double u3, v3;
                    if (!outputToFisheye(cam, o, cvRound(col), cvRound(row), u3, v3)) continue;
                    const int du = cvRound(u3) - u, dv = cvRound(v3) - v;
                    const double ei = std::hypot(du, dv);
                    cs += ec; cmax = std::max(cmax, ec); is += ei; imax = std::max(imax, ei); bu += du; bv += dv; n++;
                }
            std::ofstream f(get(m, "out", "roundtrip.txt"));
            f.precision(10);
            f << "n " << n << "\ncont_mean " << cs / n << "\ncont_max " << cmax << "\nint_mean " << is / n
              << "\nint_max " << imax << "\nbias_u " << bu / n << "\nbias_v " << bv / n
              << "\nwidth " << o.width << "\nheight " << o.height << "\n";
            std::printf("n %ld cont_max %.3e int_mean %.4f bias %.4f %.4f\n", n, cmax, is / n, bu / n, bv / n);
            if (get(m, "check", "0") == "1" && !(n > 0 && cmax < 1e-9 && std::fabs(bu / n) < 0.01 && std::fabs(bv / n) < 0.01))
                return 3;
            return 0;
        }
        if (cmd == "time") {
            cv::Mat img = cv::imread(get(m, "in", ""), cv::IMREAD_COLOR);
            if (img.empty()) throw std::runtime_error("cannot read input");
            const int reps = std::stoi(get(m, "reps", "5"));
            correct(img, cam, o);                                         // warm-up
            auto t0 = std::chrono::steady_clock::now();
            for (int k = 0; k < reps; k++) correct(img, cam, o);
            const double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count() / reps;
            std::printf("ms_per_call %.3f\nsize %d %d\nthreads %d\n", ms, o.width, o.height, cv::getNumThreads());
            return 0;
        }
        if (cmd == "viewer") {
            cv::Mat pano = cv::imread(get(m, "in", ""), cv::IMREAD_COLOR);
            if (pano.empty()) throw std::runtime_error("cannot read panorama");
            Viewer vw(pano, std::stoi(get(m, "ww", "1024")), std::stoi(get(m, "wh", "512")), num(get(m, "d", "300")));
            const int reps = std::stoi(get(m, "reps", "1"));
            cv::Mat out = vw.render(num(get(m, "aH", "0")), num(get(m, "aV", "1.5707963267948966")));
            auto t0 = std::chrono::steady_clock::now();
            for (int k = 0; k < reps; k++) out = vw.render(num(get(m, "aH", "0")), num(get(m, "aV", "1.5707963267948966")));
            const double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count() / reps;
            cv::imwrite(get(m, "out", "view.png"), out);
            std::printf("ms_per_render %.3f\n", ms);
            return 0;
        }
        if (cmd == "imgdiff") {
            cv::Mat a = cv::imread(get(m, "a", ""), cv::IMREAD_COLOR), b = cv::imread(get(m, "b", ""), cv::IMREAD_COLOR);
            if (a.empty() || b.empty()) throw std::runtime_error("cannot read a or b");
            if (a.size() != b.size()) throw std::runtime_error("size mismatch");
            cv::Mat d;
            cv::absdiff(a, b, d);
            const cv::Scalar s = cv::mean(d);
            const double mae = (s[0] + s[1] + s[2]) / 3;
            std::ifstream fa(get(m, "a", ""), std::ios::binary), fb(get(m, "b", ""), std::ios::binary);
            const std::string ba((std::istreambuf_iterator<char>(fa)), {}), bb((std::istreambuf_iterator<char>(fb)), {});
            std::printf("mae %.6f\nbyte_identical %d\n", mae, (int)(ba == bb));
            return mae <= num(get(m, "max_mae", "1")) ? 0 : 3;
        }
        if (cmd == "statics") {
            // the original getPhi1 caches h(w) in function-local statics (BUG-03); here w can change freely
            AxisMap a, b;
            a.kind = b.kind = AxisMap::LCCP;
            a.w = CV_PI / 2; b.w = CV_PI / 4;
            double worst = 0;
            for (int k = 0; k <= 1000; k++) {
                const double psi = -CV_PI / 2 + k * CV_PI / 1000;
                worst = std::max(worst, std::fabs(a.inverse(a.forward(psi)) - psi));
                worst = std::max(worst, std::fabs(b.inverse(b.forward(psi)) - psi));
            }
            std::printf("max_inverse_error_rad %.3e\n", worst);
            return worst < 1e-12 ? 0 : 1;
        }
        std::fprintf(stderr, "unknown command %s\n", cmd.c_str());
        return 2;
    } catch (const std::exception& e) {
        std::fprintf(stderr, "error: %s\n", e.what());
        return 1;                                    // non-zero exit on failure (cf. BUG-23)
    }
}
