// Non-interactive test driver for the ORIGINAL C++ sources in program/.
//
// program/ is NOT modified. The private static/member functions we need
// (getPhi, getPhi1, auxFunc, latitudeCorrection3/4/5, CircleFitByKasa, ...)
// are reached with a unity build: every system/OpenCV header is included
// first, then `private` is redefined to `public`, then the original .cpp
// files are #included verbatim. main.cpp is NOT included (it has its own
// main()); it is built separately as `navigator` by build.sh.
//
// Every subcommand writes plain text / lossless PNG so that
// research/cpp_harness/compare.py can compare it with the Python port.
#include "../../program/globalInclude.h"   // <iostream>, <opencv2/opencv.hpp>, ... (unchanged)
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <string>
#include <fstream>
#include <iomanip>
#include <chrono>

#define private public
#include "../../program/tools.cpp"
#include "../../program/findCircleParameter.cpp"
#include "../../program/corrector.cpp"
#include "../../program/imagesStitcher.cpp"
#include "../../program/viewer.cpp"
#undef private

static camMode parseModel(const std::string& s)
{
	if (s == "STEREOGRAPHIC") return STEREOGRAPHIC;
	if (s == "EQUIDISTANCE") return EQUIDISTANCE;
	if (s == "EQUISOLID") return EQUISOLID;
	if (s == "ORTHOGONAL") return ORTHOGONAL;
	std::fprintf(stderr, "unknown model %s\n", s.c_str());
	std::exit(2);
}

static void usage()
{
	std::fprintf(stderr,
		"harness getphi   H out.txt                 l=j*4/H, phi=getPhi(l)\n"
		"harness getphi1  w H out.txt               fresh statics, l=j*2auxFunc(w,0)/H\n"
		"harness static   w_first w H out.txt       getPhi1(0,w_first) once, then rows for w\n"
		"harness aux      w out.txt                 auxFunc(w, phi), phi = k*pi/2000\n"
		"harness fastatan out.txt                   cvFastArctan on a grid\n"
		"harness kasa     in.txt out.txt            CircleFitByKasa on point sets\n"
		"harness c3       img cx cy R out.png\n"
		"harness c4       img cx cy R w model fov out.png   (writes ret.jpg in cwd!)\n"
		"harness c5       img cx cy R w model fov out.png   (writes ret.jpg in cwd!)\n"
		"harness l1       img cx cy R fov Forward|Reverse out.png\n"
		"harness stitchfail                         stitchImages on 1 image (status ERR_NEED_MORE_IMGS)\n"
		"harness stitch   out.png img...            exactly main.cpp L117-142\n"
		"harness viewer   pano.png out.png          viewer::updataWindow at angleH=0, angleV=pi/2\n");
	std::exit(2);
}

int main(int argc, char** argv)
{
	if (argc < 2) usage();
	std::string cmd = argv[1];
	corrector C;

	if (cmd == "getphi" && argc == 4) {
		int H = std::atoi(argv[2]);
		std::ofstream f(argv[3]);
		f << std::setprecision(17);
		for (int j = 0; j < H; j++) {
			double l = (double)j * 4.0 / H;          // exactly as latitudeCorrection3 L615
			f << j << " " << l << " " << corrector::getPhi(l) << "\n";
		}
		return 0;
	}
	if (cmd == "getphi1" && argc == 5) {
		double w = std::atof(argv[2]);
		int H = std::atoi(argv[3]);
		std::ofstream f(argv[4]);
		f << std::setprecision(17);
		double limi = 2 * corrector::auxFunc(w, 0);  // exactly as latitudeCorrection4 L854/L881
		for (int j = 0; j < H; j++) {
			double l = (double)j * limi / H;
			f << j << " " << l << " " << corrector::getPhi1(l, w) << "\n";
		}
		return 0;
	}
	if (cmd == "static" && argc == 6) {
		double w0 = std::atof(argv[2]);
		double w = std::atof(argv[3]);
		int H = std::atoi(argv[4]);
		corrector::getPhi1(0.0, w0);                // first call initialises both statics with w0
		std::ofstream f(argv[5]);
		f << std::setprecision(17);
		double limi = 2 * corrector::auxFunc(w, 0);
		for (int j = 0; j < H; j++) {
			double l = (double)j * limi / H;
			f << j << " " << l << " " << corrector::getPhi1(l, w) << "\n";
		}
		return 0;
	}
	if (cmd == "aux" && argc == 4) {
		double w = std::atof(argv[2]);
		std::ofstream f(argv[3]);
		f << std::setprecision(17);
		for (int k = 0; k <= 2000; k++) {
			double phi = k * PI / 2000;
			f << phi << " " << corrector::auxFunc(w, phi) << "\n";
		}
		return 0;
	}
	if (cmd == "fastatan" && argc == 3) {
		std::ofstream f(argv[2]);
		f << std::setprecision(9);
		for (int a = -200; a <= 200; a++)
			for (int b = -200; b <= 200; b++) {
				float y = a * 0.37f, x = b * 0.41f;
				f << y << " " << x << " " << cvFastArctan(y, x) << "\n";
			}
		return 0;
	}
	if (cmd == "kasa" && argc == 4) {
		// input: one point set per line: "id n x1 y1 x2 y2 ..."
		std::ifstream in(argv[2]);
		std::ofstream f(argv[3]);
		f << std::setprecision(17);
		std::string id;
		int n;
		while (in >> id >> n) {
			std::vector<Point> pts(n);
			for (int k = 0; k < n; k++) in >> pts[k].x >> pts[k].y;
			Point c(-1, -1);
			int r = -1;
			bool ok = findCircleParameter::CircleFitByKasa(pts, c, r);
			f << id << " " << ok << " " << c.x << " " << c.y << " " << r << "\n";
		}
		return 0;
	}
	if ((cmd == "c3" && argc == 7) || ((cmd == "c4" || cmd == "c5") && argc == 10)) {
		Mat img = cv::imread(argv[2], cv::IMREAD_COLOR);
		if (img.empty()) { std::fprintf(stderr, "cannot read %s\n", argv[2]); return 3; }
		Point2i c(std::atoi(argv[3]), std::atoi(argv[4]));
		int R = std::atoi(argv[5]);
		Mat out;
		if (cmd == "c3") {
			auto t0 = std::chrono::steady_clock::now();
			out = C.latitudeCorrection3(img, c, R, LATITUDE_LONGTITUDE, 0, 0, PI, EQUIDISTANCE);
			std::printf("ms_latitudeCorrection3 %.3f\n", std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count());
			cv::imwrite(argv[6], out);
		} else {
			double w = std::atof(argv[6]);
			camMode m = parseModel(argv[7]);
			double fov = std::atof(argv[8]);
			if (cmd == "c4")
				out = C.latitudeCorrection4(img, c, R, PI / 2, w, LATITUDE_LONGTITUDE, 0, 0, fov, m);
			else
				out = C.latitudeCorrection5(img, c, R, PI / 2, w, LATITUDE_LONGTITUDE, 0, 0, fov, m);
			cv::imwrite(argv[9], out);
		}
		return out.empty() ? 4 : 0;
	}
	if (cmd == "l1" && argc == 9) {
		Mat img = cv::imread(argv[2], cv::IMREAD_COLOR);
		Point2i c(std::atoi(argv[3]), std::atoi(argv[4]));
		int R = std::atoi(argv[5]);
		double fov = std::atof(argv[6]);
		CorrectType t = std::string(argv[7]) == "Forward" ? Forward : Reverse;
		Mat out = C.latitudeCorrection(img, c, R, fov, t);
		cv::imwrite(argv[8], out);
		return out.empty() ? 4 : 0;
	}
	if (cmd == "stitchfail" && argc == 2) {
		// a single image: Stitcher::stitch returns ERR_NEED_MORE_IMGS (a status, not an exception),
		// so the `Stitcher::OK != status` branch of imagesStitcher.cpp L16-21 is taken.
		std::vector<Mat> imgs(1, Mat(64, 64, CV_8UC3, Scalar(10, 20, 30)));
		imagesStitcher s;
		s.stitchImages(imgs);                        // expected to fail and terminate the process
		std::printf("HARNESS: stitchImages returned normally\n");
		return 10;
	}
	if (cmd == "stitch" && argc >= 5) {
		std::vector<Mat> outputs;
		for (int k = 3; k < argc; k++) outputs.push_back(cv::imread(argv[k], cv::IMREAD_COLOR));
		std::vector<Mat> images1, images2;           // main.cpp L117-142
		for (size_t i = 0; i < outputs.size(); i++) {
			if (i < outputs.size() - 1) images1.push_back(outputs[i]);
			else images2.push_back(outputs[i]);
		}
		imagesStitcher stitcher;
		Mat tmpRet = stitcher.stitchImages(images1);
		images2.insert(images2.begin(), tmpRet.clone());
		stitcher.stitchImages(images2);
		cv::imwrite(argv[2], stitcher.getPanorama());
		std::printf("panorama %d x %d\n", stitcher.getPanorama().cols, stitcher.getPanorama().rows);
		return 0;
	}
	if (cmd == "viewer" && argc == 4) {
		Mat pano = cv::imread(argv[2], cv::IMREAD_COLOR);
		viewer v(pano);
		v.window.setTo(Scalar::all(0));               // constructor leaves it uninitialised
		auto t0 = std::chrono::steady_clock::now();
		v.updataWindow();
		std::printf("ms_updataWindow %.3f\n", std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count());
		cv::imwrite(argv[3], v.getWindow());
		return 0;
	}
	usage();
	return 2;
}
