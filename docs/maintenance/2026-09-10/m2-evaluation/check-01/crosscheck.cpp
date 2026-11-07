#define main official_main_unused
#include "/mnt/e/githouse/RAP-main/docs/maintenance/2026-09-10/m2-evaluation/devkit/devkit/cpp/evaluate_odometry.cpp"
#undef main
int main(int argc,char**argv) { auto gt=loadPoses(argv[1]); auto est=loadPoses(argv[2]); auto d=trajectoryDistances(gt); auto e=calcSequenceErrors(gt,est); for(auto v:e) printf("%d %d %.12g %.12g %.12g %.12g\n", v.first_frame,lastFrameFromSegmentLength(d,v.first_frame,v.len),v.len,v.t_err,v.r_err,v.speed); }
